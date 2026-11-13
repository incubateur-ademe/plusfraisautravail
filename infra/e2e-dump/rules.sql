-- PostgreSQL Anonymizer rules for the nightly e2e dump (see dump.sh).
--
-- EVERY column that can hold text (columns-to-declare.sql) is declared here,
-- either MASKED (personal data, secrets, internal content) or NOT MASKED
-- (public content, configuration). An undeclared column fails the CI test
-- apps/cms/tests/test_e2e_dump_rules.py, and dump.sh itself before any
-- upload. Tables listed in excluded-tables.txt are dumped without their rows
-- and are not declared.
--
-- Masked values are built from the row id, never from the real value: an
-- md5 of an e-mail would be a pseudonym, not anonymisation.
--
-- Same syntax as the extension on a live database: if the managed database
-- ever supports `anon`, this file applies as is to a masked role.

-- Masking functions, in their own schema declared TRUSTED for anon (dropped
-- by dump.sh before the final dump).
CREATE SCHEMA e2e_masks;
SECURITY LABEL FOR anon ON SCHEMA e2e_masks IS 'TRUSTED';

-- A revision is a copy of the page: form pages keep their recipients in it
-- (sites_conformes_forms_formpage below), and every page its editors'
-- comments (wagtailcore_comment below).
CREATE FUNCTION e2e_masks.revision_content(content jsonb) RETURNS jsonb
LANGUAGE sql IMMUTABLE AS $$
  SELECT CASE WHEN content ? 'to_address'
    THEN content || '{"to_address": "formulaires@example.test", "from_address": "formulaires@example.test"}'::jsonb
    ELSE content
  END - 'wagtail_admin_comments'
$$;

SECURITY LABEL FOR anon ON COLUMN auth_group.name IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN auth_permission.codename IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN auth_permission.name IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN auth_user.email IS 'MASKED WITH FUNCTION pg_catalog.concat(''user'', id, ''@example.test'')';
SECURITY LABEL FOR anon ON COLUMN auth_user.first_name IS 'MASKED WITH VALUE ''Prénom''';
SECURITY LABEL FOR anon ON COLUMN auth_user.last_name IS 'MASKED WITH FUNCTION pg_catalog.concat(''Utilisateur '', id)';
SECURITY LABEL FOR anon ON COLUMN auth_user.password IS 'MASKED WITH VALUE ''!''';
SECURITY LABEL FOR anon ON COLUMN auth_user.username IS 'MASKED WITH FUNCTION pg_catalog.concat(''user'', id)';

SECURITY LABEL FOR anon ON COLUMN cms_pages_blogentrypage.body IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN cms_pages_blogentrypage.header_color_class IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN cms_pages_blogentrypage.header_cta_buttons IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN cms_pages_blogentrypage.header_cta_text IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN cms_pages_blogentrypage.hero IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN cms_pages_blogentrypage.source_url IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN cms_pages_contentpage.body IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN cms_pages_contentpage.header_color_class IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN cms_pages_contentpage.header_cta_buttons IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN cms_pages_contentpage.header_cta_text IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN cms_pages_contentpage.hero IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN cms_pages_contentpage.source_url IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN django_admin_log.change_message IS 'MASKED WITH VALUE ''''';
SECURITY LABEL FOR anon ON COLUMN django_admin_log.object_id IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN django_admin_log.object_repr IS 'MASKED WITH FUNCTION pg_catalog.concat(''objet '', object_id)';

SECURITY LABEL FOR anon ON COLUMN django_content_type.app_label IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN django_content_type.model IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN django_migrations.app IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN django_migrations.name IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN dsfr_dsfrconfig.accessibility_status IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN dsfr_dsfrconfig.footer_brand IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN dsfr_dsfrconfig.footer_brand_html IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN dsfr_dsfrconfig.footer_description IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN dsfr_dsfrconfig.header_brand IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN dsfr_dsfrconfig.header_brand_html IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN dsfr_dsfrconfig.language IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN dsfr_dsfrconfig.newsletter_description IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN dsfr_dsfrconfig.newsletter_url IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN dsfr_dsfrconfig.notice_description IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN dsfr_dsfrconfig.notice_icon_class IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN dsfr_dsfrconfig.notice_link IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN dsfr_dsfrconfig.notice_title IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN dsfr_dsfrconfig.notice_type IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN dsfr_dsfrconfig.operator_logo_alt IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN dsfr_dsfrconfig.operator_logo_file IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN dsfr_dsfrconfig.site_tagline IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN dsfr_dsfrconfig.site_title IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN dsfr_dsfrsocialmedia.icon_class IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN dsfr_dsfrsocialmedia.title IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN dsfr_dsfrsocialmedia.url IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_blog_blogindexpage.body IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_blog_blogindexpage.header_color_class IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_blog_blogindexpage.header_cta_buttons IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_blog_blogindexpage.header_cta_text IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_blog_blogindexpage.hero IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_blog_blogindexpage.source_url IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_blog_organization.name IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_blog_organization.slug IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_blog_person.contact_info IS 'MASKED WITH VALUE ''''';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_blog_person.name IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_blog_person.role IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_catalogindexpage.body IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_catalogindexpage.filter_selection IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_catalogindexpage.header_color_class IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_catalogindexpage.header_cta_buttons IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_catalogindexpage.header_cta_text IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_catalogindexpage.hero IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_catalogindexpage.multiple_filter_operator IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_catalogindexpage.source_url IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_category.colophon IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_category.description IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_category.name IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_category.slug IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_cmsdsfrconfig.footer_brand IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_cmsdsfrconfig.footer_brand_html IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_cmsdsfrconfig.footer_description IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_cmsdsfrconfig.header_brand IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_cmsdsfrconfig.header_brand_html IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_cmsdsfrconfig.iframe_allow_origins IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_cmsdsfrconfig.language_selector_mode IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_cmsdsfrconfig.newsletter_description IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_cmsdsfrconfig.newsletter_url IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_cmsdsfrconfig.notice_description IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_cmsdsfrconfig.notice_icon_class IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_cmsdsfrconfig.notice_link IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_cmsdsfrconfig.notice_title IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_cmsdsfrconfig.notice_type IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_cmsdsfrconfig.operator_logo_alt IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_cmsdsfrconfig.operator_logo_display IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_cmsdsfrconfig.site_tagline IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_cmsdsfrconfig.site_title IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_customscriptssettings.body_scripts IS 'MASKED WITH VALUE ''''';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_customscriptssettings.head_scripts IS 'MASKED WITH VALUE ''''';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_languageselectoritem.external_url IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_languageselectoritem.language_code IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_languageselectoritem.language_name IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_languageselectoritem.link_type IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_megamenu.description IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_megamenu.main_link IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_megamenu.name IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_socialmediaitem.icon_class IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_socialmediaitem.title IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_core_socialmediaitem.url IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_customimages_customimage.description IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_customimages_customimage.file IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_customimages_customimage.file_hash IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_customimages_customimage.title IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_customimages_customrendition.file IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_customimages_customrendition.filter_spec IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_customimages_customrendition.focal_point_key IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_events_evententrypage.body IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_events_evententrypage.header_color_class IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_events_evententrypage.header_cta_buttons IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_events_evententrypage.header_cta_text IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_events_evententrypage.hero IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_events_evententrypage.location IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_events_evententrypage.registration_url IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_events_evententrypage.source_url IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_events_eventsindexpage.body IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_events_eventsindexpage.header_color_class IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_events_eventsindexpage.header_cta_buttons IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_events_eventsindexpage.header_cta_text IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_events_eventsindexpage.hero IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_events_eventsindexpage.source_url IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_faq_question.answer IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_faq_question.link_text IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_faq_question.link_url IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_faq_question.question IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_faq_theme.name IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_footer_partners_footerpartnerssettings.main_partner_alt IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_footer_partners_footerpartnerssettings.main_partner_url IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_footer_partners_footerpartnerssettings.title IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_footer_partners_partnerlogo.alt IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_footer_partners_partnerlogo.url IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_forms_formfield.autocomplete IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_forms_formfield.choices IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_forms_formfield.clean_name IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_forms_formfield.default_value IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_forms_formfield.field_type IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_forms_formfield.help_text IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_forms_formfield.label IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_forms_formpage.from_address IS 'MASKED WITH VALUE ''formulaires@example.test''';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_forms_formpage.intro IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_forms_formpage.subject IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_forms_formpage.thank_you_text IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_forms_formpage.to_address IS 'MASKED WITH VALUE ''formulaires@example.test''';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_header_logo_headerlogosettings.alt IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_menus_footerbottommenu.items IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_menus_mainmenu.items IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_menus_topmenu.items IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_proconnect_useroidc.siret IS 'MASKED WITH VALUE ''00000000000000''';
SECURITY LABEL FOR anon ON COLUMN sites_conformes_proconnect_useroidc.sub IS 'MASKED WITH FUNCTION pg_catalog.concat(''sub-'', id)';

SECURITY LABEL FOR anon ON COLUMN sites_conformes_proconnect_whitelistedemaildomain.domain IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN taggit_tag.name IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN taggit_tag.slug IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtail_notion_form_notioncontactsettings.notion_database_id IS 'MASKED WITH VALUE ''''';

SECURITY LABEL FOR anon ON COLUMN wagtailcore_collection.name IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_collection.path IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtailcore_collectionviewrestriction.password IS 'MASKED WITH VALUE ''e2e''';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_collectionviewrestriction.restriction_type IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtailcore_comment.contentpath IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_comment.position IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_comment.text IS 'MASKED WITH VALUE ''Commentaire anonymisé''';

SECURITY LABEL FOR anon ON COLUMN wagtailcore_commentreply.text IS 'MASKED WITH VALUE ''Commentaire anonymisé''';

SECURITY LABEL FOR anon ON COLUMN wagtailcore_locale.language_code IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtailcore_modellogentry.action IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_modellogentry.data IS 'MASKED WITH VALUE ''{}''';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_modellogentry.label IS 'MASKED WITH FUNCTION pg_catalog.concat(''objet '', object_id)';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_modellogentry.object_id IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtailcore_page.draft_title IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_page.path IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_page.search_description IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_page.seo_title IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_page.slug IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_page.title IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_page.url_path IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtailcore_pagelogentry.action IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_pagelogentry.data IS 'MASKED WITH VALUE ''{}''';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_pagelogentry.label IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtailcore_pageviewrestriction.password IS 'MASKED WITH VALUE ''e2e''';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_pageviewrestriction.restriction_type IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtailcore_referenceindex.content_path IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_referenceindex.model_path IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_referenceindex.object_id IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_referenceindex.to_object_id IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtailcore_revision.content IS 'MASKED WITH FUNCTION e2e_masks.revision_content(content)';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_revision.object_id IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_revision.object_str IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtailcore_site.hostname IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_site.site_name IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtailcore_task.name IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtailcore_taskstate.comment IS 'MASKED WITH VALUE ''''';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_taskstate.status IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtailcore_uploadedfile.file IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtailcore_workflow.name IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtailcore_workflowstate.object_id IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailcore_workflowstate.status IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtaildocs_document.file IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtaildocs_document.file_hash IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtaildocs_document.title IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtailembeds_embed.author_name IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailembeds_embed.hash IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailembeds_embed.html IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailembeds_embed.provider_name IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailembeds_embed.thumbnail_url IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailembeds_embed.title IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailembeds_embed.type IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailembeds_embed.url IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtailimages_image.description IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailimages_image.file IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailimages_image.file_hash IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailimages_image.title IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtailimages_rendition.file IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailimages_rendition.filter_spec IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailimages_rendition.focal_point_key IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtailmenus_flatmenu.handle IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailmenus_flatmenu.heading IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailmenus_flatmenu.title IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtailmenus_flatmenuitem.handle IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailmenus_flatmenuitem.link_text IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailmenus_flatmenuitem.link_url IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailmenus_flatmenuitem.url_append IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtailmenus_mainmenuitem.handle IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailmenus_mainmenuitem.link_text IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailmenus_mainmenuitem.link_url IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailmenus_mainmenuitem.url_append IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtailredirects_redirect.old_path IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailredirects_redirect.redirect_link IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailredirects_redirect.redirect_page_route_path IS 'NOT MASKED';

SECURITY LABEL FOR anon ON COLUMN wagtailusers_userprofile.avatar IS 'MASKED WITH VALUE ''''';
SECURITY LABEL FOR anon ON COLUMN wagtailusers_userprofile.contrast IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailusers_userprofile.current_time_zone IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailusers_userprofile.density IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailusers_userprofile.dismissibles IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailusers_userprofile.preferred_language IS 'NOT MASKED';
SECURITY LABEL FOR anon ON COLUMN wagtailusers_userprofile.theme IS 'NOT MASKED';
