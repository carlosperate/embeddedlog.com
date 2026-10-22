Title: Build static documentation from a GitHub Wiki
Date: 2015-04-20
Modified: 2015-04-20
Category: Blog
Tags: github, documentation, web
Slug: static-docs-from-github-wiki
Lang: en
banner_image: static-docs-from-github-wiki.jpg
Summary: Documentation websites can be created using static site generators and markdown files, but did you ever wish anybody contributing to you project could access an easy to use markdown editor without additional services or accounts? GitHub Wikis offers just that, and the markdown files can be accessed via git. So we can use the GitHub Wiki editor and combine it with a static site generator to create our documentation website.


One of the goals of [Ardublockly][1], specially taking in consideration that it is based on web technologies, is to be deployable to offline systems without additional dependencies. For its documentation [GitHub Wikis][2] was chosen, as it is easy to use, can be viewed and edited directly from the GitHub website, and integrates quite well with its [GitHub repository][3]. So a way to provide offline access to this documentation was required, and because the project build procedure is based on Python, a solution using this language was preferred.

[MkDocs][4] turned out to be a perfect fit for this purpose. MkDocs is a static site generator, based on Markdown files (GitHub Wiki's default format) and tailored specifically for documentation.

So this article will cover the installation, configuration and automation of static documentation from a GitHub Wiki using MkDocs.

Contents:

[TOC]


## Installing MkDocs

MkDocs can be easily installed using pip (as with any other Python project, it is highly recommended to use [virtual environments][5]):

```
pip install mkdocs
```


## Creating a MkDocs project and adding the Wiki content

Navigate to the folder where the project files are to be saved and then execute in the console:

```
mkdocs new my-project
```

This will create the new `mkdocs` project folder, where the documentation content must also be saved, so navigate inside it to clone the GitHub Wiki repository.

In the case of the Ardublockly project, it was saved within a git repository already, so a [Git Submodule][6] was used instead of a simple `git clone`.

```
git clone https://github.com/<username>/<repository>.wiki.git
```

OR

```
git submodule add https://github.com/<username>/<repository>.wiki.git
```

(Don't forget to replace `<username>` and `<repository>` with your own information.)


## Configure the MkDocs project

Now the MkDocs configuration file `mkdocs.yml` has to be edited to point to the new content folder by setting the `docs_dir` property.

Open the `mkdocs.yml` file, which would already contain the `site_name` property and add the wiki files directory (remember to surround the directory string with single quotation marks):
```yaml
site_name: 'Documentation Title'

docs_dir: '<wiki folder directory>'
```

Other project properties can also be added, refer to the [MkDoc documentation][7] for more information.

MkDocs requires all the markdown files to be generated listed under the `pages` property. We can automate this step later using a Python script, so for this specific example the `pages` property should be placed at the very end of the `mkdocs.yml` file (with all your current files), ideally with a warning:

```yaml
# It is IMPERATIVE to leave this property to the end without anything after it.
# This is because the build file will delete everything after this line and
# replace it with newly generated data. 
pages:
- ['index.md', 'Home']
```


## Test the static page generator

MkDocs comes with a handy built-in web server that lets you preview the generated content live.

Navigate to the MkDocs project folder and execute the following command:

```
mkdocs serve
```

This will serve the pages at: `http://127.0.0.1:8000/`

Make sure there is an `index.md` to generate the `index.html` file, and check if everything has been rendered as expected.

To deploy the pages you can build the project, into the default `site` folder, using the following command:
```
mkdocs build
```


## Create a Python build script

Now that we have a static HTML version of the Wiki markdown files, we can start looking into automating with Python all the steps required to update these files.

First let's predefine some path and repository data, this will depend on your own environment and repository information, so remember to fill the missing information. For this example the build file was included on the parent directory of the MkDocs project folder:

```python
GITHUB_USER = ""
WIKI_NAME = ""
GITHUB_WIKI_REPO = "github.com/%s/%s.git" % (GITHUB_USER, WIKI_NAME)

MKDOCS_FOLDER = ""
THIS_FILE_DIR = os.path.dirname(os.path.realpath(__file__))
MKDOCS_DIR = os.path.join(THIS_FILE_DIR, MKDOCS_FOLDER)
```

For the sake of simplicity a lot of the exception handling and error management has been left out of these code snippets, but a more comprehensive source file is linked in the [Conclusion](#Conclusion).

### Git Pull the latest changes

The first step to update the documentation is to pull the latest changes from the wiki repository. For this task the script will use subprocesses and assumes that Git is installed on the system:

```python
import os
import subprocess


def pull_wiki_repo():
    """ Pulls latest changes from the wiki repo. """
    # Set working directory to the wiki repository
    wiki_folder = os.path.join(MKDOCS_DIR, WIKI_NAME)
    os.chdir(wiki_folder)

    # Ensure the subfolder selected is the correct repository
    PIPE = subprocess.PIPE
    git_process = subprocess.Popen(["git", "config", "--get", "remote.origin.url"], stdout=PIPE, stderr=PIPE)
    std_op, std_err_op = git_process.communicate()
    if not GITHUB_WIKI_REPO in std_op:
        print("Wiki repository:\n\t%s\nnot found in url:\n\t%s\n" %
              (GITHUB_WIKI_REPO, std_op))
    else:
        print("Pull from Wiki repository...")
        subprocess.call(["git", "pull", "origin", "master"])
```

If using a submodule within a git repository, as the Ardublockly project is, remember to ensure the submodule has been initialised and updated.

Keep in mind that this function changes the current working directory, so any other function that depends on this value (e.g. using relative directories) might be affected.


### Edit MkDocs configuration file

As previously mentioned, MkDocs requires all the markdown files to be listed in the `mkdocs.yml` file, which is why the `pages` property was left at the end of it. The following python function scans `mkdocs.yml` until the `pages:` line is encountered and it then auto-generates the list:

```python
import os
import shutil
from tempfile import mkstemp


def edit_mkdocs_config():
    """
    Edits the mkdocs.yml MkDocs configuration file to include all markdown
    files as part of the documentation.
    These files are created by default with the '.md' extension and it is 
    assumed no other file extensions are to be linked.
    """
    path_list = []
    for file in os.listdir(os.path.join(MKDOCS_DIR, WIKI_NAME)):
        if file.endswith(".md"):
            path_list.append("- ['%s', '%s']" % (file, file[:-3].replace("-", " ")))
    pages_str = "pages:\n" + "\n".join(path_list) + "\n"

    # Replace the pages data, strategically located at the end of the file
    mkdocs_yml = os.path.join(MKDOCS_DIR, "mkdocs.yml")
    temp_file_handler, temp_abs_path = mkstemp()
    with open(temp_abs_path, 'w') as temp_file:
        with open(mkdocs_yml) as original_file:
            for line in original_file:
                if not "pages:" in line:
                    temp_file.write(line)
                else:
                    print("Replacing 'pages' property found in mkdocs.yml ...")
                    break
            else:
                print("Did not find the 'pages' property in mkdocs.yml.\n" +
                      "Attaching the property at the end of the file.")
            temp_file.write(pages_str)
            print(pages_str)

    # Remove original file and move the new temp to replace it
    os.close(temp_file_handler)
    os.remove(mkdocs_yml)
    move(temp_abs_path, mkdocs_yml)
```

The main three code blocks, separated by a blank line, do the following:

1. Scans the wiki repository directory for any file with the `.md` extension (default for markdown), and adds it to a string for the `pages` property.
2. Creates a temporary file to which it copies all the lines from the original `mkdocs.yml` file until it reads the `pages:` line. Once it reaches this line it stops copying and adds the string built on the previous code block.
3. Removes the original `mkdocs.yml` file and replaces it by the newly created file with the updated `pages` data.


### Build MkDocs

Similarly to the git procedure, MkDocs will be built using a subprocess. After that, the site folder is moved into a different location, this step is relevant to the current exampli and can be removed, or edited to your own preferences:

```python
import os
import shutil


def build_mkdocs():
    """
    Invokes MkDocs to build the static documentation and moves the folder
    into the project root folder.
    """
    # Setting the working directory
    os.chdir(MKDOCS_DIR)

    # Building the MkDocs project
    subprocess.call(["mkdocs", "build"])

    # Remove root Documentation folder and copy the new site files into it
    generated_site_dir = os.path.join(MKDOCS_DIR, "site")
    root_documentation_dir = os.path.join(os.path.dirname(THIS_FILE_DIR), "documentation")
    print("Copy folder %s into %s ...\n" % (generated_site_dir, root_documentation_dir))

    if os.path.exists(root_documentation_dir):
        shutil.rmtree(root_documentation_dir)
    shutil.move(generated_site_dir, root_documentation_dir)
```


### Add Index redirect

GitHub Wiki will create by default a `Home` article for the homepage with the filename `Home.md` (article titles are automatically used for their markdown filename). Having an `index.md` file for MkDocs to automatically set as the `index.html` page would require having a wiki article titled "Index", which is not a helpul article title for users. So, in order to continue using the GitHub Wiki as intended the build procedure could create an `index.html` file to redirect to a predefined page.

For this example the HTML file will redirect to the `Home` page created from the default 'Home.md' markdown file:

```python
import os

DEFAULT_INDEX = 'Home'

def create_index():
    """ Creates an HTML index page to redirect to an MkDocs generated page. """
    html_code = \
        "<!DOCTYPE HTML>\n " \
        "<html>\n" \
        "\t<head>\n" \
        "\t\t<meta charset=\"UTF-8\">\n" \
        "\t\t<meta http-equiv=\"refresh\" content=\"1;url=%s/index.html\">\n" \
        % DEFAULT_INDEX + \
        "\t\t<script type=\"text/javascript\">\n" \
        "\t\t\twindow.location.href = \"%s/index.html\"\n" % DEFAULT_INDEX +\
        "\t\t</script>\n" \
        "\t</head>\n" \
        "\t<body>\n" \
        "\t\tIf you are not redirected automatically to the " \
        "%s page, follow this <a href=\"%s/index.html\">link</a>\n"\
        % (DEFAULT_INDEX, DEFAULT_INDEX) + \
        "\t</body>\n" \
        "</html>\n"

    print("Creating the index.html file...\n")
    generated_site_dir = os.path.join(MKDOCS_DIR, "site", "index.html")
    index_file = open(generated_site_dir, "w")
    index_file.write(html_code)
    index_file.close()
```

The HTML code has been embedded into the Python function, so that it can be reconstructed from scratch without depending on an additional file. This function will create the `index.html` file at the root of the `site` folder, and automatically redirect to whatever page has been set in `DEFAULT_INDEX`.


## Conclusion

And we are done! We have a simple way to build offline static documentation from a GitHub Wiki, all easily achieved using Python, Git, and MkDocs!

Most of the heavy lifting has been done by the fantastic [MkDocs][4], and the build script created just speeds up the process by pulling the latest changes from the Wiki git repository, updating the MkDocs configuration file, and redirecting your homepage to maintain your GitHub documentation workflow the same.

For a more practical code example you can have a look at the [Ardublockly documentation build script][8], which also does some error and exception handling for a more robust build process.


[1]: http://www.embeddedlog.com/ardublockly/index.html
[2]: https://github.com/carlosperate/ardublockly/wiki
[3]: https://github.com/carlosperate/ardublockly
[4]: http://www.mkdocs.org
[5]: http://docs.python-guide.org/en/latest/dev/virtualenvs
[6]: http://git-scm.com/docs/git-submodule
[7]: http://www.mkdocs.org/user-guide/configuration/
[8]: https://github.com/carlosperate/ardublockly/blob/d68bce4651fa23a63666b558d7cd4be5336067d5/package/build_docs.py
