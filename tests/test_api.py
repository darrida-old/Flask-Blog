import unittest
import json
import re
from base64 import b64encode
from app import create_app, db
from app.models import User, Role, Post, Comment
from app.fake import posts

class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def get_api_headers(self, username, password):
        return {
            'Authorization': 'Basic ' + b64encode(
                    (username + ':' + password).encode('utf-8')).decode('utf-8'),
                'Accept': 'appliation/json',
                'Content-Type': 'application/json'
        }
            
    def test_no_auth(self):
        response = self.client.get('/api/v1/posts/', 
                                   content_type='application/json')
        self.assertEqual(response.status_code, 401)
        
    def test_posts(self):
        # add a user
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='john@example.com', password='cat', confirmed=True,
                 role=r)
        db.session.add(u)
        db.session.commit()
        
        # write a post
        response = self.client.post(
                '/api/v1/posts/',
                headers=self.get_api_headers('john@example.com', 'cat'),
                data=json.dumps({'body': 'body of the *blog* post'}))
        self.assertEqual(response.status_code, 201)
        url = response.headers.get('location')
        self.assertIsNotNone(url)
        
        # get the new post
        response = self.client.get(
                url,
                headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual('http://localhost' + json_response['url'], url)
        self.assertEqual(json_response['body'], 'body of the *blog* post')
        self.assertEqual(json_response['body_html'],
                         '<p>body of the <em>blog</em> post</p>')
        
        # edit the new post
        response = self.client.put(
                url,
                headers=self.get_api_headers('john@example.com', 'cat'),
                data=json.dumps({'body': 'body of *changed* post'}))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(url)
        self.assertEqual(json_response['body'], 'body of *changed* post')
        self.assertEqual(json_response['body_html'],
                         '<p>body of <em>changed</em> post</p>')
        
        # post count, posts exist, next
        posts(count=25)
        response = self.client.get(
                '/api/v1/posts/',
                headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['count'], 26)
        self.assertEqual(json_response['next_url'], '/api/v1/posts/?page=2')
        self.assertIsNotNone(json_response['posts'])
        self.assertEqual(json_response['prev_url'], None)
        next_url = json_response['next_url']
        
        # use next page button
        response = self.client.get(
                next_url,
                headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['count'], 26)
        self.assertEqual(json_response['next_url'], None)
        self.assertIsNotNone(json_response['posts'])
        self.assertEqual(json_response['prev_url'], '/api/v1/posts/?page=1')
        prev_url = json_response['prev_url']
        edit_url = json_response['posts'][0]['url'] #for edit authentication failed
        
        # use previous page button
        response = self.client.get(
                prev_url,
                headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['next_url'], '/api/v1/posts/?page=2')
        
        # test edit authentication failed
        ######################################################
        # add user that didn't exist when any post was randomly created
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='bill@example.com', password='cat', confirmed=True,
                 role=r)
        db.session.add(u)
        db.session.commit()
        ######################################################
        
        response = self.client.put(
                edit_url,
                headers=self.get_api_headers('bill@example.com', 'cat'),
                data=json.dumps({'body': 'failed to edit another\'s post'}))
        self.assertEqual(response.status_code, 403)
        json_response = json.loads(response.get_data(as_text=True))
        
    def test_comments(self):
        # add a user
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='john@example.com', password='cat', confirmed=True,
                 role=r)
        db.session.add(u)
        db.session.commit()
        
        # write a post (to then comment on)
        response = self.client.post(
                '/api/v1/posts/',
                headers=self.get_api_headers('john@example.com', 'cat'),
                data=json.dumps({'body': 'comment created'}))
        self.assertEqual(response.status_code, 201)
        url = response.headers.get('location')
        self.assertIsNotNone(url)
        json_response = json.loads(response.get_data(as_text=True))
        url_comments = 'http://localhost' + json_response['url'] + '/comments/'
        
        # post new comment
        #url = url + '/comments/'
        response = self.client.post(
                url_comments,
                headers=self.get_api_headers('john@example.com', 'cat'),
                data=json.dumps({'body': 'body of the *comment*'}))
        self.assertEqual(response.status_code, 201)
        url = response.headers.get('location')
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual('http://localhost' + json_response['url'], url)
        self.assertEqual(json_response['body'], 'body of the *comment*')
        self.assertEqual(json_response['body_html'],
                         '<p>body of the <em>comment</em></p>')
        
    def test_users(self):
        # add a user
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='john@example.com', password='cat', username='username match',
                 confirmed=True, role=r)
        db.session.add(u)
        db.session.commit()
        
        # get the new user
        response = self.client.get(
                '/api/v1/users/1',
                headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        #url = response.headers.get('location')
        #print(url)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['username'], 'username match')
        
        # get user posts
        response = self.client.get(
                'http://localhost' + json_response['posts_url'],
                headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['count'], 0)
        self.assertEqual(json_response['next'], None)
        self.assertEqual(json_response['posts'], [])
        self.assertEqual(json_response['prev'], None)
        