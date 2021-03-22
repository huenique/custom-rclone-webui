===================
Custom-Rclone-WebUI
===================

Custom web-based GUI for Rclone that features a simple 
interface and options to automate standard rclone commands 
in the background.

NOTE: Rclone wrapper only supports Windows for now.

Setup
-----------
Download Rclone from https://rclone.org/downloads/ 
and add the executable to your environment variables.

From inside the custom-rclone-webui directory, run:

.. code-block:: bash

    pip install .

Quick start
-----------

1. Navigate to custom_rclone_webui or the directory containing 
   the manage.py file.

2. Run ``python manage.py makemigrations`` to create new migrations.

3. Run ``python manage.py migrate`` to apply migrations 
   and to create the webui model.

4. Start the development server with ``python manage.py runserver`` 
   and visit http://127.0.0.1:8000/.