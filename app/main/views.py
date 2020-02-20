from flask import render_template, redirect, url_for, current_app, \
                  flash, request, make_response, abort, jsonify
from flask_login import login_required, current_user, login_user
from flask_sqlalchemy import get_debug_queries
from sqlalchemy import func
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm
from .. import db
from ..models import User, Role, Post, Permission, Comment, postTag, activePost
from ..decorators import admin_required, permission_required
from datetime import datetime, tzinfo
from tzlocal import get_localzone


@main.route('/', methods=['GET', 'POST'])
def index():
    page = request.args.get('page', 1, type=int)
    active_posts_query = db.session.query(func.max(Post.id)) \
                                            .group_by(Post.activePost_id)
    post_list = []
    for tuple in active_posts_query:
        for item in tuple:
            post_list.append(item)
    query = db.session.query(Post).filter(Post.id.in_((post_list))).filter(Post.published==True)
    pagination = query.order_by(Post.timestamp.desc()).paginate(
            page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
            error_out=False)
    posts = pagination.items
    return render_template('index.html', posts=posts,
                           show_followed=show_followed, pagination=pagination)


@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    url_post_id = db.session.query(func.max(Post.id)).filter(Post.activePost_id==id).first()
    post = Post.query.get_or_404(url_post_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash('You comment has been published.')
        return redirect(url_for('.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    # FIXME: Comments are BROKEN
    if page == -1:
        page = (post.comments.count() - 1) // \
                current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
            page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
            error_out=False)
    comments = pagination.items
    return render_template('post.html', posts=[post], form=form,
                           comments=comments, pagination=pagination)


@main.route('/search', methods=['GET', 'POST'])
def search(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        search_entry = Post.query.title('*' + form.search.data + '*')
        flash('You comment has been published.')
        return redirect(url_for('.search_results', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // \
                current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
            page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
            error_out=False)
    comments = pagination.items
    return render_template('post.html', posts=[post], form=form,
                           comments=comments, pagination=pagination)


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
            page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
            error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments,
                           pagination=pagination, page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))


@main.route('/edit/new', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def edit_new():
    # CLEAN: The if statement is only needed with empty posts table, which is extremely rare
    #        and probably only happens once... ever.
    if Post.query.all() == []:
        max_post_id = 1
    else:
        max_post_id = db.session.query(func.max(Post.activePost_id)).first()[0] + 1
    new_post = Post(title="", body="", published=0, activePost_id=max_post_id, author=current_user._get_current_object())
    db.session.add(new_post)
    db.session.flush()
    db.session.refresh(new_post)
    if request.method=='POST' and request.form['submit']=='Close':
        flash('Closed without updating or saving.')
        db.session.rollback()
        return redirect(url_for('.manage_posts'))
    elif request.method=='POST' and current_user.can(Permission.WRITE):
        if request.form['title'] == "" and request.form['body'] == "":
            flash('Title and Body required')
            return redirect(url_for('.edit', id=0))
        else:
            new_post.title = request.form['title']
            new_post.body = request.form['body']
            new_post.published = (0 if request.form['submit'] == 'Save' else 1)
            db.session.add(new_post)
            db.session.flush()
            db.session.refresh(new_post)
            db.session.commit()
            if request.form['submit'] == 'Save':
                return redirect(url_for('.edit', id=new_post.activePost_id))
            else:
                flash('The post has been updated and published.')
            if request.form['submit'] == 'Publish & Close':
                return redirect(url_for('.post', id=new_post.activePost_id))
    form = PostForm()
    form.title.data = new_post.title
    form.body.data = new_post.body
    form.id.data = new_post.id
    form.post_type.data = 'new'
    form.status.data = 'Not Saved'
    action = 'Create'
    return render_template('edit_post.html', action=action, form=form)


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def edit(id):
    form = None
    url_post_id = db.session.query(func.max(Post.id)).filter(Post.activePost_id==id).first()
    post = Post.query.get_or_404(url_post_id)
    if post.id == None:
        flash('Post not found')
        return redirect(url_for('.manage_posts'))
    #else:
    #    post = Post.query.filter_by(id=url_id.post_id).first()
#CLEAN I think I can use "history" to count versions rather than the "versions" query further below (thus only do 1 query instead of 2)
#      Actually, I can probably use the html string creation from the "draft_save" function below and get rid of interating with jinja2 altogther
    history = Post.query.filter(Post.activePost_id==id).filter(Post.id != url_post_id[0]).order_by(Post.timestamp_edited.desc()).all()
    new_post = Post(title=post.title, 
                    body=post.body,
                    published=post.published,
                    activePost_id = post.activePost_id,
                    author=post.author)
    db.session.add(new_post)
    db.session.flush()
    db.session.refresh(new_post)
    current = post.id
    
    if current_user != post.author and not current_user.can(Permission.ADMIN):
        abort(403)   
    if request.method=='POST' and request.form['submit']=='Close':
        flash('The post was not updated.')
        db.session.rollback()
        return redirect(url_for('.manage_posts'))
    elif request.method=='POST' and current_user.can(Permission.WRITE):
        if request.form['title'] == "" and request.form['body'] == "":
            flash('Title and Body required')
            return redirect(url_for('.edit', id=0))
        else:
            new_post.title = request.form['title']
            new_post.body = request.form['body']
            new_post.published = (0 if request.form['submit'] == 'Save Draft' else 1)
            new_post.activePost_id = post.activePost_id
            db.session.add(new_post)
            db.session.flush()
            db.session.refresh(new_post)
            db.session.commit()
            if request.form['submit'] == 'Save Draft':
                flash('The post has been updated as a draft.')
                return redirect(url_for('.edit', id=new_post.activePost_id))
            else:
                flash('The post has been updated and published.')
            if request.form['submit'] == 'Publish & Close':
                return redirect(url_for('.post', id=new_post.activePost_id))
    form = PostForm()
    form.title.data = post.title
    form.body.data = post.body
    form.id.data = post.id
    form.active_post.data = post.activePost_id
    form.post_type.data = 'edit'
    if post.published == 1:
        form.status.data = 'Published'
    elif post.published == 0:
        form.status.data = 'Saved Draft'
    action = 'Edit'
    #BEGIN Counts number number of revisions that exist for this post - displays total as the "current" revision number
    versions = Post.query.filter_by(activePost_id=post.activePost_id).all()
    version_number = 0
    for version in versions:
        version_number += 1
    #END
    return render_template('edit_post.html', action=action, form=form,
#CLEAN The "-1" is because the function creates a post in memory and flushes it to send it to the db without committing.
#      I believe any code that actually commits to the db in this function can be removed, because of the now existing 
#      jquery functionality.
                            history=history, post=post, version_number=version_number - 1)


@main.route('/history/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def edit_history(id):
    form = None
    post = Post.query.get_or_404(id)
    if post.id == None:
        flash('Post not found')
        return redirect(url_for('.manage_posts'))
    if current_user != post.author and not current_user.can(Permission.ADMIN):
        abort(403)   
    if request.method=='POST' and request.form['submit']=='Close':
        return redirect(url_for('.manage_posts'))
    elif request.method=='POST' and current_user.can(Permission.WRITE):
        if request.form['title'] == "" and request.form['body'] == "":
            flash('Title and Body required')
            return redirect(url_for('.edit', id=0))
        else:
            if request.form['submit'] == 'Save Draft':
                flash('The post has been updated as a draft.')
                return redirect(url_for('.edit', id=post.id))
            else:
                flash('The post has been updated and published.')
            if request.form['submit'] == 'Publish & Close':
                return redirect(url_for('.post', id=post.id))
    form = PostForm()
    form.title.data = post.title
    form.body.data = post.body
    form.id.data = post.id
    form.active_post.data = post.activePost_id
    form.post_type.data = 'history'
    if post.published == 1:
        form.status.data = 'Published'
    elif post.published == 0:
        form.status.data = 'Saved Draft'
    action = 'History'
    return render_template('edit_post_history.html', action=action, form=form, timestamp=post.timestamp_edited, id=id)
    
@main.route('/_quick_save', methods=['GET'])
@login_required
@permission_required(Permission.WRITE)
def quick_save():
    post_id=request.args.get('post_id', 0, type=int)
    post = Post.query.get_or_404(post_id)
    post.published=(False if request.args.get('post_status', 0, type=str)=='Saved Draft' else True)
    post.title=request.args.get('post_title', 0, type=str)
    post.body=request.args.get('post_body', 0, type=str)
    post.timestamp_edited=datetime.utcnow()
    db.session.add(post)
    db.session.commit()
    return jsonify(result="Last save: " + str(datetime.now().strftime("%I:%M:%S")))


@main.route('/_published_switch')
@login_required
@permission_required(Permission.WRITE)
def published_switch():
    post_id=request.args.get('post_id', 0, type=int)
    post = Post.query.get_or_404(post_id)
    post.published=(True if post.published==0 else False)
    post.title=request.args.get('post_title', 0, type=str)
    post.body=request.args.get('post_body', 0, type=str)
    post.timestamp_edited=datetime.utcnow()
    db.session.add(post)
    db.session.flush()
    db.session.refresh(post)
    db.session.commit()
    versions = Post.query.filter_by(activePost_id=post.activePost_id).all()
    number = 0
    for version in versions:
        number += 1
    print(number)
    publish_switch = ("Unpublish" if post.published==1 else "Publish")
    publish_state = ("Status: Saved Draft" if post.published==0 else "Status: Published")
    return jsonify(result="Last save: " + str(datetime.now().strftime("%I:%M:%S")),
                   published_switch=f"{publish_switch}",
                   post_status=publish_state)


@main.route('/_draft_save')
@login_required
@permission_required(Permission.WRITE)
def draft_save():
    # FIXME: When creating a new post and this option is selected it doesn't create a new post.
    #        Instead it creates a new revision of an existing post (it may just create a new revision
    #        of whatever the highest blog post number is at the time). This needs to be fixed before I 
    #        can use this to create blog posts.
    max_post_id = db.session.query(func.max(Post.activePost_id)).first()[0]
    new_post_version = Post()
    new_post_version.published=(False if request.args.get('published_status', 0, type=str)==False else True)
    new_post_version.title=request.args.get('post_title', 0, type=str)
    new_post_version.body=request.args.get('post_body', 0, type=str)
    new_post_version.activePost_id=max_post_id  
    new_post_version.author=current_user._get_current_object()
    new_post_version.timestamp=datetime.utcnow()
    new_post_version.timestamp_edited=datetime.utcnow()
    db.session.add(new_post_version)
    db.session.flush()
    db.session.refresh(new_post_version)
    db.session.commit()
    #BEGIN Create updated history list as html string to past back to the page
    history = Post.query.filter(Post.activePost_id==new_post_version.activePost_id).filter(Post.id != new_post_version.id).order_by(Post.timestamp_edited.desc()).all()
    history_html = """"""
    for item in history:
        history_html = history_html + f"""
            <li><a data-toggle="modal" href="#myModal{item.id}"></a>
                <a href="/history/{item.id}" target="_blank">
                    <span class="" data-refresh="0" style="">{item.timestamp_edited.strftime('%Y/%m/%d, %I:%M %p')}</span>
                </a>
            </li>"""
    #END
    #BEGIN Counts number number of revisions that exist for this post - displays total as the "current" revision number
    #TODO Can use info from here to reduce this to one line:
    #     https://stackoverflow.com/questions/34692571/how-to-use-count-in-flask-sqlalchemy to 
    versions = Post.query.filter_by(activePost_id=new_post_version.activePost_id).all()
    version_number = 0
    for version in versions:
        version_number += 1
    #END
    post_id=new_post_version.id
    post = Post.query.get_or_404(post_id)
    new_published = ("Saved Draft" if post.published==0 else "Published")
    return jsonify(post_id=post.id, 
                   post_title=post.title, 
                   post_body=post.body, 
                   published=f"Status: {new_published}",
                   timestamp=f"Created: {post.timestamp.strftime('%Y/%m/%d, %I:%M %p')} "
                           + f"| Last edit: {post.timestamp_edited.strftime('%Y/%m/%d, %I:%M %p')}",
                   version_number=version_number,
                   history=history_html)


@main.route('/manage', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def manage_posts():
    page = request.args.get('page', 1, type=int)
    show_followed = False
    if current_user.is_authenticated:
        show_followed = False
    active_posts_query = db.session.query(func.max(Post.id)) \
                                              .group_by(Post.activePost_id)
    post_list = []
    for tuple in active_posts_query:
        for item in tuple:
            post_list.append(item)
    query = db.session.query(Post).filter(Post.id.in_((post_list)))#.filter(Post.published==True)

    pagination = query.order_by(Post.timestamp.desc()).paginate(
            page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
            error_out=False)
    posts = pagination.items
    return render_template('manage_posts.html', posts=posts,
                           show_followed=show_followed, pagination=pagination)

    
@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=user, posts=posts)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)  # 30 days
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)  # 30 days
    return resp

# @main.route('/shutdown')
# def server_shutdown():
#     if not current_app.testing:
#         abort(404)
#     shutdown = request.environ.get('werkzeug.server.shutdown')
#     if not shutdown:
#         abort(500)
#     shutdown()
#     return 'Shutting down...'