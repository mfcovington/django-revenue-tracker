**********************
django-revenue-tracker
**********************

``django-revenue-tracker`` is a Django app to track transactions, royalties, and revenues.

Source code is available on GitHub at `mfcovington/django-revenue-tracker <https://github.com/mfcovington/django-revenue-tracker>`_.

.. contents:: :local:


Installation
============

.. **PyPI**

.. .. code-block:: sh

..     pip install django-revenue-tracker


**GitHub (development branch)**

.. code-block:: sh

    pip install git+http://github.com/mfcovington/django-revenue-tracker.git@develop


Configuration
=============

Add ``revenue_tracker`` to ``INSTALLED_APPS`` in ``settings.py``:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'django.contrib.humanize',
        'ordered_model',
        'crispy_forms',
        'tempus_dominus',
        'djmoney',
        'customer_tracker',
        'dropbox_file_tracker',
        'project_home_tags',
        'ngs_project_tracker',
        'revenue_tracker',
    )


Specify the following in ``settings.py``:

.. code-block:: python

    ROYALTY_PERCENTAGE = 0.025    # This setting, for example, represents a 2.5% royalty rate
    PHONENUMBER_DEFAULT_REGION = 'US'
    CRISPY_TEMPLATE_PACK = 'bootstrap4'
    DROPBOX_ACCESS_TOKEN = ''    # https://www.dropbox.com/developers/apps
    DROPBOX_APP_KEY = ''    # https://www.dropbox.com/developers/apps
    BRANDING_NAME = ''    # e.g., BRANDING_NAME = 'Amaryllis Nucleics'
    MEDIA_URL = '/files/'    # Replace '/files/' with preferred URL
    MEDIA_ROOT = os.path.join(BASE_DIR, 'files')    # Replace 'files' with preferred path


If using ``project_home_tags`` in your project, specify the ``PROJECT_HOME_NAMESPACE`` and, optionally, ``PROJECT_HOME_LABEL`` in ``settings.py`` (see `PyPI <https://pypi.org/project/django-project-home-templatetags/>`_ for more information):

.. code-block:: python

    PROJECT_HOME_NAMESPACE = 'project_name:index_view'
    PROJECT_HOME_LABEL = 'Homepage'    # Optional; Default is 'Home'


Add the ``revenue_tracker``, ``ngs_project_tracker``, and ``dropbox_file_tracker`` URLs to the site's ``urls.py``:

.. code-block:: python

    from django.conf import settings
    from django.conf.urls.static import static
    from django.urls import include, path

    urlpatterns = [
        ...
        path('dropbox/', include('dropbox_file_tracker.urls', namespace='dropbox-file-tracker')),
        path('projects/', include('ngs_project_tracker.urls', namespace='ngs-project-tracker')),
        path('transactions/', include('revenue_tracker.urls', namespace='revenue_tracker')),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


Create the Dropbox thumbnails directory

.. code-block:: sh

    python manage.py mkdir_thumbnails


Migrations
==========

Create migrations for ``revenue_tracker`` and dependencies, if necessary:

.. code-block:: sh

    python manage.py makemigrations customer_tracker
    python manage.py makemigrations dropbox_file_tracker
    python manage.py makemigrations ngs_project_tracker
    python manage.py makemigrations revenue_tracker


Perform migrations for ``revenue_tracker`` and dependencies:

.. code-block:: sh

    python manage.py migrate


Usage
=====

- Start the development server:

.. code-block:: sh

    python manage.py runserver

- Visit to set base prices for various transaction types: ``http://127.0.0.1:8000/admin/revenue_tracker/baseprice/``


*Version 0.2.1*
