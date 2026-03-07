from django.urls import path
from content.views.contact import contact_list, new_contact
from content.views.design import design_list
from content.views.model_3d import model3d_list
from content.views.product import product_list
from content.views.hosting import hosting_list
from content.views.portfolio_works import portfolio_works_list
from content.views.proposal import (
    retrieve_public_proposal, download_proposal_pdf,
    list_proposals, retrieve_proposal, create_proposal,
    create_proposal_from_json, get_proposal_json_template,
    update_proposal, delete_proposal, send_proposal,
    resend_proposal, toggle_proposal_active,
    update_proposal_section, bulk_reorder_sections,
    respond_to_proposal, check_admin_auth,
)
from content.views.blog import (
    list_blog_posts, retrieve_blog_post,
    list_admin_blog_posts, create_blog_post, create_blog_post_from_json,
    get_blog_json_template,
    retrieve_admin_blog_post, update_blog_post, delete_blog_post,
)

urlpatterns = [
    path('contacts/', contact_list, name='contact-list'),
    path('designs/', design_list, name='design-list'),
    path('models3d/', model3d_list, name='model3d-list'),
    path('products/', product_list, name='product-list'),
    path('hostings/', hosting_list, name='hosting-list'),
    path('portfolio_works/', portfolio_works_list, name='portfolio-works-list'),
    path('new-contact/', new_contact, name='new-contact'),

    # Proposals — public
    path('proposals/<uuid:proposal_uuid>/', retrieve_public_proposal, name='retrieve-public-proposal'),
    path('proposals/<uuid:proposal_uuid>/pdf/', download_proposal_pdf, name='download-proposal-pdf'),
    path('proposals/<uuid:proposal_uuid>/respond/', respond_to_proposal, name='respond-to-proposal'),

    # Proposals — admin auth check
    path('auth/check/', check_admin_auth, name='check-admin-auth'),

    # Proposals — admin CRUD
    path('proposals/', list_proposals, name='list-proposals'),
    path('proposals/create/', create_proposal, name='create-proposal'),
    path('proposals/create-from-json/', create_proposal_from_json, name='create-proposal-from-json'),
    path('proposals/json-template/', get_proposal_json_template, name='proposal-json-template'),
    path('proposals/<int:proposal_id>/detail/', retrieve_proposal, name='retrieve-proposal'),
    path('proposals/<int:proposal_id>/update/', update_proposal, name='update-proposal'),
    path('proposals/<int:proposal_id>/delete/', delete_proposal, name='delete-proposal'),
    path('proposals/<int:proposal_id>/send/', send_proposal, name='send-proposal'),
    path('proposals/<int:proposal_id>/resend/', resend_proposal, name='resend-proposal'),
    path('proposals/<int:proposal_id>/toggle-active/', toggle_proposal_active, name='toggle-proposal-active'),
    path('proposals/<int:proposal_id>/reorder-sections/', bulk_reorder_sections, name='reorder-sections'),

    # Proposals — section editing
    path('proposals/sections/<int:section_id>/update/', update_proposal_section, name='update-proposal-section'),

    # Blog — admin CRUD (must come before slug catch-all)
    path('blog/admin/', list_admin_blog_posts, name='list-admin-blog-posts'),
    path('blog/admin/create/', create_blog_post, name='create-blog-post'),
    path('blog/admin/create-from-json/', create_blog_post_from_json, name='create-blog-post-from-json'),
    path('blog/admin/json-template/', get_blog_json_template, name='blog-json-template'),
    path('blog/admin/<int:post_id>/detail/', retrieve_admin_blog_post, name='retrieve-admin-blog-post'),
    path('blog/admin/<int:post_id>/update/', update_blog_post, name='update-blog-post'),
    path('blog/admin/<int:post_id>/delete/', delete_blog_post, name='delete-blog-post'),

    # Blog — public
    path('blog/', list_blog_posts, name='list-blog-posts'),
    path('blog/<slug:slug>/', retrieve_blog_post, name='retrieve-blog-post'),
]
