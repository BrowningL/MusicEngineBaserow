"""
Management command to set up Supabase SSO provider.

Usage:
    python manage.py setup_supabase_sso \
        --supabase-url=https://xxx.supabase.co \
        --supabase-anon-key=eyJ... \
        --template-workspace-id=133

Or with environment variables:
    SUPABASE_URL=https://xxx.supabase.co \
    SUPABASE_ANON_KEY=eyJ... \
    BASEROW_TEMPLATE_WORKSPACE_ID=133 \
    python manage.py setup_supabase_sso
"""

import os

from django.core.management.base import BaseCommand, CommandError

from baserow.contrib.supabase_sso.models import SupabaseAuthProviderModel


class Command(BaseCommand):
    help = 'Set up or update the Supabase SSO provider configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--supabase-url',
            type=str,
            default=os.getenv('SUPABASE_URL'),
            help='Supabase project URL (e.g., https://xxx.supabase.co)',
        )
        parser.add_argument(
            '--supabase-anon-key',
            type=str,
            default=os.getenv('SUPABASE_ANON_KEY'),
            help='Supabase anon/public key',
        )
        parser.add_argument(
            '--template-workspace-id',
            type=int,
            default=int(os.getenv('BASEROW_TEMPLATE_WORKSPACE_ID', '0')) or None,
            help='Workspace ID to duplicate templates from for new users',
        )
        parser.add_argument(
            '--disable',
            action='store_true',
            help='Disable the SSO provider instead of enabling it',
        )

    def handle(self, *args, **options):
        supabase_url = options['supabase_url']
        supabase_anon_key = options['supabase_anon_key']
        template_workspace_id = options['template_workspace_id']
        disable = options['disable']

        if not supabase_url:
            raise CommandError(
                'Supabase URL is required. Set SUPABASE_URL env var or use --supabase-url'
            )

        if not supabase_anon_key:
            raise CommandError(
                'Supabase anon key is required. Set SUPABASE_ANON_KEY env var or use --supabase-anon-key'
            )

        # Get or create the provider
        provider, created = SupabaseAuthProviderModel.objects.get_or_create(
            defaults={
                'name': 'Supabase SSO',
                'enabled': not disable,
                'supabase_url': supabase_url,
                'supabase_anon_key': supabase_anon_key,
                'auto_provision_workspace': True,
                'template_workspace_id': template_workspace_id,
                'default_workspace_name_template': "{name}'s Workspace",
            }
        )

        if not created:
            # Update existing provider
            provider.supabase_url = supabase_url
            provider.supabase_anon_key = supabase_anon_key
            provider.enabled = not disable
            if template_workspace_id:
                provider.template_workspace_id = template_workspace_id
            provider.save()
            action = 'Updated'
        else:
            action = 'Created'

        self.stdout.write(
            self.style.SUCCESS(
                f'{action} Supabase SSO provider:\n'
                f'  - ID: {provider.id}\n'
                f'  - Name: {provider.name}\n'
                f'  - Enabled: {provider.enabled}\n'
                f'  - Supabase URL: {provider.supabase_url}\n'
                f'  - Template Workspace ID: {provider.template_workspace_id}\n'
                f'  - Auto Provision: {provider.auto_provision_workspace}'
            )
        )
