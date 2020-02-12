# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# import threading
# import time
# import re
# import unittest
# from app import create_app, db, fake
# from app.models import Role, User, Post


# class SeleciumTestCase(unittest.TestCase):
#     client = None
    
#     @classmethod
#     def setUpClass(cls):
#         # start Chrome
#         options = Options()
#         #options = webdriver.ChromeOptions()
#         options.headless = True
#         #options.log.level = "trace"
#         options.add_argument('--headless')
#         options.add_argument('--no-proxy-server')
#         options.add_argument("--proxy-server='direct://'")
#         options.add_argument("--proxy-bypass-list=*")
#         #options.set_windows_size(1440, 900)
#         try:
#             cls.client = webdriver.Chrome(r'C:\Users\benha\Documents\Development\chromedriver\chromedriver.exe', chrome_options=options)
#         except:
#             cls.client = webdriver.Chrome(r'C:\local-work\GitHub\flask-book-sample-app\flasky\utilities\chromedriver78\chromedriver.exe', chrome_options=options)
#         finally:
#             pass

#         # skip these tests if the browser could not be started
#         if cls.client:
#             # create the application
#             cls.app = create_app('testing')
#             cls.app_context = cls.app.app_context()
#             cls.app_context.push()

#             # suppress logging to keep unittest output clean
#             import logging
#             logger = logging.getLogger('werkzeug')
#             logger.setLevel("ERROR")

#             # create the database and populate with some fake data
#             db.create_all()
#             Role.insert_roles()
#             fake.users(10)
#             fake.posts(10)

#             # add an administrator user
#             admin_role = Role.query.filter_by(name='Administrator').first()
#             admin = User(email='john@example.com',
#                          username='john', password='cat',
#                          role=admin_role, confirmed=True)
#             db.session.add(admin)
#             db.session.commit()

#             # start the Flask server in a thread
#             cls.server_thread = threading.Thread(target=cls.app.run,
#                                                  kwargs={'debug': False})
#             cls.server_thread.start()

#             # give the server a second to ensure it is up
#             time.sleep(1) 
            
#     @classmethod
#     def tearDownClass(cls):
#         if cls.client:
#             # stop the Flask server and the browser
#             cls.client.get('http://localhost:5000/shutdown')
#             cls.client.quit()
#             cls.server_thread.join()
            
#             # destroy database
#             db.drop_all()
#             db.session.remove()
            
#             # remove application context
#             cls.app_context.pop()
            
#     def setUp(self):
#         if not self.client:
#            self.skipTest('Web browser not available')
#         pass
    
#     def tearDown(self):
#         pass
    
#     def test_admin_home_page(self):
#         # navigate to home page
#         self.client.get('http://localhost:5000/')
#         #print(self.client.page_source)
#         time.sleep(3) 
#         self.assertTrue(re.search('Hello,\s+Stranger!',
#                                   self.client.page_source))
        
#         # navigate to login page
#         self.client.find_element_by_link_text('Log In').click()
#         self.assertIn('<h1>Login</h1>', self.client.page_source)
        
#         # log in
#         time.sleep(3)
#         self.client.find_element_by_name('email').send_keys('john@example.com')
#         self.client.find_element_by_name('password').send_keys('cat')
#         self.client.find_element_by_name('submit').click()
#         time.sleep(3)
#         self.assertTrue(re.search('Hello,\s+john!', self.client.page_source))
        
#         # navigate to the user's profile page
#         self.client.find_element_by_link_text('Profile').click()
#         self.assertIn('<h1>john</h1>', self.client.page_source)