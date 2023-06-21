# django-dropbox-app
A django demo application that integrates with the Dropbox API. The app allows you to display the contents of a Dropbox account and perform basic file operations such as downloading, uploading, and deleting files and folders and creating new folders. To use the app, you need to provide it with access to a Dropbox account.

## Prerequisites
- Python (version 3.6 or above) and pip installed on your system.
- Basic knowledge of Django framework.
- A Dropbox account.

## Installation
  1.Clone the repository or download the source code for the Django Dropbox demo app.  
  ```bash
  $ git clone git@github.com:Kihara-Njoroge/django-dropbox-app.git
  ```
  2.Change into the project directory.
  ```bash
   $ cd django-dropbox-app
  ```
  3.It is recommended to create a virtual environment for the project to isolate the dependencies.
  ```bash
  $ python3 -m venv env
  ```
  4.Activate the virtual environment.
  . On macOS and Linux:
  ```bash
    $ source env/bin/activate
  ```
  . On Windows:
  ```bash
    $ .\env\Scripts\activate
  ```
  5.Install the required dependencies using pip.
  ```bash
    $ pip install -r requirements.txt
  ```
6. Configuration

    - Create a Dropbox app and obtain the API credentials:
        - Go to the [Dropbox App Console](https://www.dropbox.com/developers/apps/create).
        - Choose the "Scoped access" option.
        - Select the following permissions:
            - files.metadata.read (to read the contents of the Dropbox account)
            - files.content.read (to download files from the Dropbox account)
            - files.content.write (to upload files to the Dropbox account)
            - files.content.delete (to delete files from the Dropbox account)
        - Generate an access token for your app.

    - Rename the `.env.example` file to `.env`.

    - Open the `.env` file and update the following configurations:
        - `DROPBOX_OAUTH2_TOKEN`: Paste the access token obtained from the Dropbox app.
        - `DROPBOX_APP_KEY`: Paste the app key obtained from the Dropbox app.


          
## Running the App
  1.Start the development server.
  ```bash
    $ python3 -m venv env
  ```
  2. Open your web browser and access the app at http://localhost:8000 or as per the URL displayed in the terminal.
  3. You will see a login page. Click on the "Allow" button to authenticate the app with your Dropbox account.
  4. Once authenticated, you will be able to view the contents of your Dropbox account and perform file operations such as           downloading, uploading, and deleting files and folders and create new folders.




  





