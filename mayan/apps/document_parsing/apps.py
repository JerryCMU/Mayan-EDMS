from __future__ import unicode_literals

import logging
from datetime import timedelta

from django.apps import apps
from django.db.models.signals import post_save
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from kombu import Exchange, Queue

from mayan.apps.acls import ModelPermission
from mayan.apps.common import (
    MayanAppConfig, menu_facet, menu_multi_item, menu_object, menu_secondary,
    menu_tools
)
from mayan.apps.common.classes import ModelAttribute, ModelField
from mayan.apps.common.settings import settings_db_sync_task_delay
from mayan.apps.documents.search import document_page_search, document_search
from mayan.apps.documents.signals import post_version_upload
from mayan.apps.documents.widgets import document_link
from mayan.apps.navigation import SourceColumn
from mayan.celery import app

from .events import event_parsing_document_version_submit
from .handlers import (
    handler_index_document, handler_initialize_new_parsing_settings,
    handler_parse_document_version
)
from .links import (
    link_document_content, link_document_content_download,
    link_document_page_content, link_document_parsing_errors_list,
    link_document_submit, link_document_submit_multiple,
    link_document_type_parsing_settings, link_document_type_submit,
    link_error_list
)
from .permissions import (
    permission_content_view, permission_document_type_parsing_setup,
    permission_parse_document
)
from .signals import post_document_version_parsing
from .utils import document_property_content, get_document_content

logger = logging.getLogger(__name__)


def document_parsing_submit(self):
    latest_version = self.latest_version
    # Don't error out if document has no version
    if latest_version:
        latest_version.submit_for_parsing()


def document_version_parsing_submit(self):
    from .tasks import task_parse_document_version

    event_parsing_document_version_submit.commit(
        action_object=self.document, target=self
    )

    task_parse_document_version.apply_async(
        eta=now() + timedelta(seconds=settings_db_sync_task_delay.value),
        kwargs={'document_version_pk': self.pk},
    )


class DocumentParsingApp(MayanAppConfig):
    app_namespace = 'document_parsing'
    app_url = 'parsing'
    has_rest_api = True
    has_tests = True
    name = 'mayan.apps.document_parsing'
    verbose_name = _('Document parsing')

    def ready(self):
        super(DocumentParsingApp, self).ready()

        Document = apps.get_model(
            app_label='documents', model_name='Document'
        )
        DocumentPage = apps.get_model(
            app_label='documents', model_name='DocumentPage'
        )
        DocumentType = apps.get_model(
            app_label='documents', model_name='DocumentType'
        )
        DocumentTypeSettings = self.get_model(
            model_name='DocumentTypeSettings'
        )
        DocumentVersion = apps.get_model(
            app_label='documents', model_name='DocumentVersion'
        )
        DocumentVersionParseError = self.get_model(
            model_name='DocumentVersionParseError'
        )

        Document.add_to_class('submit_for_parsing', document_parsing_submit)
        Document.add_to_class(
            'content', document_property_content
        )
        DocumentVersion.add_to_class(
            'content', get_document_content
        )
        DocumentVersion.add_to_class(
            'submit_for_parsing', document_version_parsing_submit
        )

        ModelAttribute(
            model=Document, name='content', description=_(
                'The parsed content of the document.'
            )
        )

        ModelField(
            Document, name='versions__pages__content__content'
        )

        ModelPermission.register(
            model=Document, permissions=(
                permission_content_view, permission_parse_document
            )
        )
        ModelPermission.register(
            model=DocumentType, permissions=(
                permission_document_type_parsing_setup,
            )
        )
        ModelPermission.register_inheritance(
            model=DocumentTypeSettings, related='document_type',
        )

        SourceColumn(
            source=DocumentVersionParseError, label=_('Document'),
            func=lambda context: document_link(context['object'].document_version.document)
        )
        SourceColumn(
            source=DocumentVersionParseError, label=_('Added'),
            attribute='datetime_submitted'
        )
        SourceColumn(
            source=DocumentVersionParseError, label=_('Result'),
            attribute='result'
        )

        app.conf.task_queues.append(
            Queue('parsing', Exchange('parsing'), routing_key='parsing'),
        )

        app.conf.task_routes.update(
            {
                'mayan.apps.document_parsing.tasks.task_parse_document_version': {
                    'queue': 'parsing'
                },
            }
        )

        document_search.add_model_field(
            field='versions__pages__content__content', label=_('Content')
        )

        document_page_search.add_model_field(
            field='content__content', label=_('Content')
        )

        menu_facet.bind_links(
            links=(link_document_content,), sources=(Document,)
        )
        menu_facet.bind_links(
            links=(link_document_page_content,), sources=(DocumentPage,)
        )
        menu_multi_item.bind_links(
            links=(link_document_submit_multiple,), sources=(Document,)
        )
        menu_object.bind_links(
            links=(link_document_submit,), sources=(Document,)
        )
        menu_object.bind_links(
            links=(link_document_type_parsing_settings,), sources=(DocumentType,),
            position=99
        )
        menu_secondary.bind_links(
            links=(
                link_document_content, link_document_parsing_errors_list,
                link_document_content_download
            ),
            sources=(
                'document_parsing:document_content',
                'document_parsing:document_content_download',
                'document_parsing:document_parsing_error_list',
            )
        )
        menu_tools.bind_links(
            links=(
                link_document_type_submit, link_error_list,
            )
        )

        post_document_version_parsing.connect(
            dispatch_uid='document_parsing_handler_index_document',
            receiver=handler_index_document,
            sender=DocumentVersion
        )
        post_save.connect(
            dispatch_uid='document_parsing_handler_initialize_new_parsing_settings',
            receiver=handler_initialize_new_parsing_settings,
            sender=DocumentType
        )
        post_version_upload.connect(
            dispatch_uid='document_parsing_handler_parse_document_version',
            receiver=handler_parse_document_version,
            sender=DocumentVersion
        )
