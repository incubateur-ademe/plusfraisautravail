"""Follow sites-conformes moving Category from its blog app to core, and naming the
blog entry categories ``categories``, on the swapped-in BlogEntryPage.

The category table itself is renamed in place by sites_conformes_blog.0068, so the
foreign keys only change in the migration state. This must run before
sites_conformes_blog.0069 drops Category from the blog app's state.
"""

import django.db.models.deletion
import modelcluster.fields
from django.db import migrations, models
from sites_conformes.core.migration_utils import rename_revision_field


class Migration(migrations.Migration):
    dependencies = [
        ("cms_pages", "0002_blogentrypage"),
        ("sites_conformes_core", "0087_category"),
    ]
    run_before = [
        ("sites_conformes_blog", "0069_category_to_core_state"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="categoryentrypage",
                    name="category",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="sites_conformes_core.category",
                        verbose_name="Catégorie",
                    ),
                ),
                migrations.AlterField(
                    model_name="blogentrypage",
                    name="blog_categories",
                    field=modelcluster.fields.ParentalManyToManyField(
                        blank=True,
                        through="cms_pages.CategoryEntryPage",
                        to="sites_conformes_core.category",
                        verbose_name="Catégories",
                    ),
                ),
            ],
        ),
        migrations.RenameField(model_name="blogentrypage", old_name="blog_categories", new_name="categories"),
        migrations.RunPython(*rename_revision_field("cms_pages", "BlogEntryPage", "blog_categories", "categories")),
    ]
