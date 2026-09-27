===============================================
  BELMONT COUNTY MUGSHOT HELPER
  Simple instructions for beginners
===============================================

This app runs on YOUR computer only.
No one else can see it. It is completely private.

-----------------------------------------------
STEP 1 – Install Python (one-time setup)
-----------------------------------------------

1. Go to this website:  https://www.python.org/downloads/
2. Click the big yellow button that says "Download Python".
3. Run the installer.
4. IMPORTANT: On the first screen of the installer,
   CHECK the box that says "Add Python to PATH".
5. Click "Install Now" and wait until it finishes.

-----------------------------------------------
STEP 2 – Download this app folder
-----------------------------------------------

You should have a folder called "belmont_mugshot_app".
Put it somewhere easy to find, for example on your Desktop.

-----------------------------------------------
STEP 3 – Open the Command Prompt / Terminal
-----------------------------------------------

Windows:
  - Press the Windows key
  - Type "cmd" and press Enter
  - A black window will open

Mac:
  - Press Command + Space
  - Type "Terminal" and press Enter

-----------------------------------------------
STEP 4 – Go into the app folder
-----------------------------------------------

In the black window, type the following and press Enter
(change the path if you put the folder somewhere else):

Windows example:
  cd Desktop\belmont_mugshot_app

Mac example:
  cd Desktop/belmont_mugshot_app

-----------------------------------------------
STEP 5 – Install the needed tools (one-time)
-----------------------------------------------

Type this and press Enter:

  pip install -r requirements.txt

Wait until it finishes (it may take a minute).

-----------------------------------------------
STEP 6 – Start the app
-----------------------------------------------

Type this and press Enter:

  python app.py

You should see a message that says:

  Open your browser to:  http://127.0.0.1:5000

-----------------------------------------------
STEP 7 – Open the app in your browser
-----------------------------------------------

1. Open Chrome, Edge, or Firefox
2. In the address bar type exactly:

   http://127.0.0.1:5000

3. Press Enter

You will see the app page.

-----------------------------------------------
HOW TO USE THE APP
-----------------------------------------------

- Click the blue button "Check for New Inmates Now"
- The app will look at the public Belmont County roster
- Any new people will appear as cards with a photo and text
- You can copy the text and the photo to post on Facebook yourself
- Posts stay in the list for 24 hours
- You can mark them Approved or Discard them

The app also checks automatically every hour
while it is running.

To stop the app: go back to the black window
and press Ctrl + C

-----------------------------------------------
NEED HELP?
-----------------------------------------------

If something does not work, copy the exact error
message that appears in the black window and
ask for help.

===============================================
