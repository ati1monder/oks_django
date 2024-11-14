from django.urls import path

from . import views

urlpatterns = [
    # adminpanel login and logout
    path('login/', views.login_view, name='admin_login'),
    path('', views.admin_index_view, name='admin_index'),
    path('logout', views.logout_view, name='admin_logout'),

    # users tab
    path('users/', views.user_view, name='users'),
    path('users/<int:userid>', views.user_details_view, name='user'),
    path('users/<int:userid>/edit', views.user_edit_view, name='user_edit'),
    path('users/<int:userid>/edit/new_subcription', views.user_new_subscription_view, name='user_new_subscription'),
    path('users/<int:userid>/delete', views.user_delete_view, name='user_delete'),

    # courses online tab
    path('courses_online/', views.courses_online_view, name='courses_online'),
    path('courses_online/<int:classid>', views.course_online_details_view, name='courses_online_details_view'),
    path('courses_online/<int:classid>/delete', views.course_online_delete, name='delete_online_course'),
    path('courses_online/<int:classid>/edit', views.course_online_edit, name='edit_online_course'),
    path('courses_online/new', views.course_online_create, name='create_online_course'), # new online course
    path('courses_online/new/future', views.course_online_create_future, name='create_online_future_course'), # online courses in advance
    
    # courses offline tab
    path('courses_offline/', views.courses_offline_view, name='courses_offline'),
    path('courses_offline/<int:classid>', views.course_offline_details_view, name='courses_offline_details_view'),
    path('courses_offline/<int:classid>/delete', views.course_offline_delete, name='delete_offline_course'),
    path('courses_offline/<int:classid>/edit', views.course_offline_edit, name='edit_offline_course'),
    path('courses_offline/new', views.course_offline_create, name='create_offline_course'),

    # YA YEBAV CIU HUETU
    path('courses_online/new/callback', views.zoom_oauth_callback, name='zoom_oauth_callback'),
    path('create-meeting/', views.create_zoom_meeting, name='create_zoom_meeting'),

    # video tab
    path('video', views.video_view, name="video_index"),
    path('video/<int:videoid>', views.video_details_view, name="video_details"),
    path('video/<int:videoid>/edit', views.video_details_edit_view, name="video_edit"),
    path('video/<int:videoid>/delete', views.video_delete_view, name="video_delete"),
    path('video/new', views.new_video_view, name='new_video'),
    path('video/tags', views.video_tags_view, name="video_tags"),
    path('video/tags/<int:tagid>/delete', views.video_tag_delete_view, name="tag_delete"),
    path('video/tags/new', views.new_tag_view, name='new_tag'),

    # settings tab
    path('settings', views.settings_view, name='settings'), # sales and the day of opened doors
    path('settings/online_sale', views.online_sale_view, name="online_sale"),
    path('settings/offline_sale', views.offline_sale_view, name="offline_sale"),
    path('settings/subscription', views.edit_subscription_view, name="edit_subscription"),
    path('settings/edit_access_day', views.edit_access_day_view, name="edit_access_day"),

    # retreat
    path('retreat/', views.retreat_index_view, name='retreat_index'),
    path('retreat/edit_text', views.retreat_edit_description_view, name='retreat_edit_text'),
    path('retreat/upload/', views.upload_image_view, name='upload_image'),
    path('retreat/delete/<int:imageid>', views.delete_image_view, name='delete_image'),
    path('retreate/delete/registrations', views.retreat_delete_registrations, name='delete_registrations'),
    
]