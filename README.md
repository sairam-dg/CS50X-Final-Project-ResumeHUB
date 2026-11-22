# ResumeHub: your one stop resume builder

#### Video Demo: <YouTube URL>

## Description

ResumeHub is a web application that lets a user build a professional resume
through simple forms, preview it live in the browser, and download it as a PDF.
Each user can create and manage their resume using their account, and their resume is stored in a database, so they can
log in at any time to edit it thus making sure that they do not lose any data or have to start from scratch.

I built it because most resume tools either hide the PDF behind a paywall or
produce layouts that applicant tracking systems (ATS) cannot read. ResumeHub
uses a single-column, text-based layout that is ATS-friendly.

### Features

- Register, log in and log out (passwrods are hashed before storage, thus facilitating better security)
- One resume per user, with six fixed sections: contact, summary, education,
  experience, skills and projects
- All the details can be edited and updated through simple forms.
- Add, edit and delete entries for education, experience and projects
- Dashboard shows the progress of each section
- Resume preview in the browser
- One-click PDF download
- Responsive design for all devices.

## Tech stack

- Python 3, Flask
- Flask-Login for session management
- SQLite, accessed through the CS50 library ('cs50.SQL')
- Jinja2 templates, HTML and CSS
- Playwright (headless Chromium) for PDF generation
- python-dotenv for configuration

## How to run

1. Install the requirements:
   
   python -m pip install -r requirements.txt
   python -m playwright install chromium
   
2. Create a `.env` file in the project folder containing a secret key:
   
   SECRET_KEY=<any long random string>
   
   You can generate one with
   python -c "import secrets; print(secrets.token_hex(16))".
3. Create the database from the schema:

   sqlite3 resumehub.db < schema.sql
   
   On Windows PowerShell use `Get-Content schema.sql | sqlite3 resumehub.db`.
4. Start the app:
   
   python app.py
   
5. Open http://127.0.0.1:5000 in a browser.


### File descriptions

**app.py** contains the Flask application and all routes: authentication,
dashboard, the edit pages, preview and download. The education, experience and
projects sections share one set of routes, driven by a `SECTIONS` dictionary
that records each section's table, primary key, fields and required fields.
It also includes the helper functions that fetch entries and assemble the data, which the resume template needs.

**models.py** defines the `User` class (based on Flask-Login's `UserMixin`) and
the functions that look a user up by id or username. Flask-Login needs a `User`
object, but `cs50.SQL` returns plain dictionaries, so this file bridges the two.

**extensions.py** creates the `LoginManager` and the `user_loader` callback moreover, 
it is kept separate from `app.py` to avoid circular imports.

**schema.sql** holds the `CREATE TABLE` statements for the seven tables:
`users`, `contact`, `summary`, `education`, `experience`, `projects` and `skills`.

**utils/db.py** creates the single shared database connection.

**utils/pdf.py** turns the rendered resume HTML into a PDF using Playwright.

**templates/base.html** is the shared layout (navigation bar, flash messages).
Every other page extends it.

**templates/edit/** contains one template per resume section. The education,
experience and projects templates each handle both "add new" and "edit existing".

**templates/resume/resume_template.html** is the resume itself. It does not
extend `base.html`, so it contains no navigation, and the same file is used for
both the browser preview and the PDF.

**static/css/style.css** styles the website. **static/css/resume.css** styles
only the resume, including the print and page-size rules.

## Design choices

- **One resume per user, fixed sections.** A user needs one good resume that is
  easy to update. This removed the need for a resumes table and "which resume
  am I editing" logic, and it keeps the interface simple.
- **Schema design.** `contact` and `summary` are one-to-one with users, so
  `user_id` is their primary key, which makes duplicate rows impossible.
  Education, experience, projects and skills are one-to-many, so each has its
  own id and a `user_id` foreign key.
- **Dates stored as text.** SQLite has no real date type, and a resume needs
  values such as "Present", so dates are plain text.
- **Ownership checks.** Every query for an entry includes `AND user_id = ?`
  with the logged-in user's id. A user who guesses another user's entry id gets
  a 404 and never sees that data.
- **One generic set of routes.** Education, experience and projects are the
  same pattern with different fields, so a `SECTIONS` dictionary drives one set
  of routes instead of three near-identical copies. The table and column names
  in the SQL come only from this dictionary, never from user input.
- **Same template for preview and PDF.** Editing the layout in one file changes
  both. The preview toolbar is shown only on `/preview`, so it never appears in
  the PDF.
- **Separate stylesheets.** The resume's CSS has to be print-safe, while the
  site's CSS can change freely. Keeping them apart means a site restyle can
  never break the PDF.
- **Single-column layout.** It is easier to print correctly and is read more
  reliably by ATS software than multi-column designs.
- **Playwright instead of WeasyPrint.** I first chose WeasyPrint, but it needs
  system libraries (Pango) that are awkward to install on Windows. Playwright
  uses a real browser engine, so the PDF matches the preview closely and no
  system libraries are needed. The cost is a one-time browser download.
- **Flask-Login with cs50.SQL.** I wanted exposure to a real session library
  while keeping the raw SQL style from the course.
- **Plain forms, no JavaScript.** Adding an entry is a normal form post and a
  page reload. This kept the app simple and reliable.

## Security notes

- Passwords are hashed with Werkzeug's `generate_password_hash`.
- All SQL uses `?` placeholders to prevent SQL injection.
- Jinja2 escapes output automatically, which protects against script injection.
- Every page except the home, login and register pages requires login.
- The secret key lives in `.env` and is never committed.

## Future scope

These are ideas I have **not** implemented yet.

- **AI assistant that fills in the resume.** The user would paste or type their
  project briefs, achievements and certificates into a chat box, and an
  assistant would extract the details and fill in the forms for them. Planned
  approach:
  1. A chat page where the user types free text.
  2. The text is sent to a language model with a prompt asking for output in a
     fixed JSON structure that matches the database columns.
  3. The app validates the JSON, then shows the result as a pre-filled draft.
  4. The user reviews and edits the draft, and only then is it saved. Nothing
     is written to the database without the user's approval, because a model
     can misread or invent details.
  5. A new `certificates` table and resume section to hold certificates.
- Live preview while editing
- Multiple resume templates
- Drag-and-drop section ordering and custom sections
- Optional import from LinkedIn or an existing PDF

## AI assistance

i used Claude (Anthropic) as a learning and coding aid. The idea was original as described above, but AI helped me with the implementation and helped me in refining the details. I used it to generate boilerplate codee, to suggest improvements, debug and explain code, and to help me properly decribe my work in the readme. I did not use it to generate the whole project without any understanding on my part. Every part of code was read and reviewd by me and understood completely before intergrating into the project. Thus it was not used to generate the logic, but only to help me implement it.  