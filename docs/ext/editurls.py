import os
import warnings


def edit_github_url(app, path):
    return 'https://github.com/{project}/edit/{branch}/docs/{path}'.format(
        project=app.config.github_doc_edit_project,
        branch=app.config.github_doc_edit_branch,
        path=path)


def html_page_context(app, pagename, templatename, context, doctree):
    if templatename != 'page.html':
        return

    if not app.config.github_doc_edit_project:
        warnings.warn("github_doc_edit_project not specified")
        return

    path = os.path.relpath(doctree.get('source'), app.builder.srcdir)

    edit_url = edit_github_url(app, path)

    context['edit_url'] = edit_url


def setup(app):
    app.add_config_value('github_main_dev_project', '', True)
    app.add_config_value('github_main_dev_branch', '', True)
    app.add_config_value('github_doc_edit_project', '', True)
    app.add_config_value('github_doc_edit_branch', '', True)
    app.connect('html-page-context', html_page_context)
