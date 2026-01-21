from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('baserow_core_auth_provider', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupabaseAuthProviderModel',
            fields=[
                ('authprovidermodel_ptr', models.OneToOneField(
                    auto_created=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    parent_link=True,
                    primary_key=True,
                    serialize=False,
                    to='baserow_core_auth_provider.authprovidermodel'
                )),
                ('supabase_url', models.URLField(
                    help_text='Supabase project URL (e.g., https://xxx.supabase.co)'
                )),
                ('supabase_anon_key', models.CharField(
                    help_text='Supabase anon/public key for API access',
                    max_length=512
                )),
                ('jwks_url', models.URLField(
                    blank=True,
                    default='',
                    help_text='JWKS URL for JWT validation. Defaults to {supabase_url}/auth/v1/.well-known/jwks.json'
                )),
                ('auto_provision_workspace', models.BooleanField(
                    default=True,
                    help_text='Automatically create workspace for new users'
                )),
                ('template_workspace_id', models.IntegerField(
                    blank=True,
                    help_text='Workspace ID to duplicate templates from for new users',
                    null=True
                )),
                ('default_workspace_name_template', models.CharField(
                    default="{name}'s Workspace",
                    help_text="Template for new workspace names. Use {name} for user's name.",
                    max_length=255
                )),
            ],
            options={
                'verbose_name': 'Supabase Auth Provider',
                'verbose_name_plural': 'Supabase Auth Providers',
            },
            bases=('baserow_core_auth_provider.authprovidermodel',),
        ),
        migrations.CreateModel(
            name='SupabaseUserMapping',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID'
                )),
                ('supabase_user_id', models.CharField(
                    db_index=True,
                    help_text='Supabase user UUID (sub claim from JWT)',
                    max_length=255,
                    unique=True
                )),
                ('supabase_email', models.EmailField(
                    help_text='Email from Supabase (for reference/debugging)',
                    max_length=254
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_login_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='supabase_mapping',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Supabase User Mapping',
                'verbose_name_plural': 'Supabase User Mappings',
            },
        ),
    ]
