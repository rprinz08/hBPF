# Welcome to hBPF contributing guide

Thank you for investing your time in contributing to the hBPF
project!

Read our [Code of Conduct](CODE_OF_CONDUCT.md) to keep our community approachable and respectable.

In this guide you will get an overview of the contribution
workflow from opening an issue, creating a PR, reviewing, and
merging the PR.

## New contributor guide

To get an overview of the project, read the [README](README.md) first. Here are some resources to help you get started
with open source contributions in general:

- [Finding ways to contribute to open source on GitHub](https://docs.github.com/en/get-started/exploring-projects-on-github/finding-ways-to-contribute-to-open-source-on-github)
- [Set up Git](https://docs.github.com/en/get-started/quickstart/set-up-git)
- [GitHub flow](https://docs.github.com/en/get-started/quickstart/github-flow)
- [Collaborating with pull requests](https://docs.github.com/en/github/collaborating-with-pull-requests)

## Getting started

### Issues

#### Create a new issue

If you spot a functional problem somewhere in the project,
first search if an [issue already exists](https://github.com/rprinz08/hBPF/issues).

If a related issue doesn't exist, you can open a new issue
using the [issue form](https://github.com/rprinz08/hBPF/issues/new).

Explain the problem and include additional details to help us reproduce the problem:

* **Use a clear and descriptive title** for the issue to identify the problem using english language.
* **Describe the exact steps which reproduce the problem** in as many details as possible.
* **Provide specific examples to demonstrate the steps**. Include links to files or GitHub projects, or copy/pasteable snippets, which you use in those examples. If you're providing snippets in the issue, use [Markdown code blocks](https://help.github.com/articles/markdown-basics/#multiple-lines).
* **Describe the behavior you observed after following the steps** and point out what exactly is the problem with that behavior.
* **Explain which behavior you expected to see instead and why.**
* **Describe the used hardware** like FPGA boards, hardware devices etc. possibly including schematics.
* **Include screenshots, pictures or videos** to provide additional information like waveforms on an oscilloscope or logic-analyzer.

_Note: Changes that are cosmetic in nature and do not add
anything substantial to the stability, functionality, or
testability of hBPF will generally not be accepted. We
appreciate it when these things are found in our code, but
this creates some hidden cost like:_
* _Someone need to spend the time to review the patch.
However trivial the changes might seem, there might be some
subtle reasons the original code are written this way and any
tiny changes have the possibility of altering behavior and
introducing bugs._
* _It pollutes the git history. When someone need to
investigate a bug and `git blame` these lines in the future,
they'll hit this "refactor" commit which is not very useful._
* _It makes backporting bug fixes harder._

#### Solve an issue

Scan through our [existing issues](https://github.com/rprinz08/hBPF/issues) to find one that interests you. We would be very happy if you came up with a solution for it.

### Make Changes

## Submitting changes

Please send a [GitHub Pull Request to hBPF](https://github.com/rprinz08/hbpf/pull/new/main) with a clear list of what
you've done (read more about [pull requests](http://help.github.com/pull-requests/)).

When you send a pull request, we would be very happy if you
include detailed information what you have done. Please
follow our coding conventions (below) and make sure all of
your commits are atomic (one feature per commit).

### Testing changes

Before submitting your changes ensure that ALL tests included
in hBPF complete successfully. In case of a new feature,
please include everything to test it (e.g. a corresponding test case, scripts, config files etc.).

### How to commit your change

* Fork the hBPF project on Github.

* Clone the fork to your local machine.

* Make your changes.

* Add the file(s) you have modified to the staging area using:

    ```
    $ git add .
    $ git add <filename>
    ```

* Commit and write what changes you have made in the commit
  message using:

    ```
    $ git commit -m "<YOUR NAME>: <TASK>"
    e.g. commit -m "JohnDow: Add new XYZ feature"
    ```

* Always write a clear log message for your commits. One-line
messages are fine for small changes, but bigger changes
should look like this:

    ```
    $ git commit -m "A brief summary of the commit
    >
    > A paragraph describing what changed and its impact."
    ```

* Create a [pull request](http://help.github.com/pull-requests/).

### Working with branches

Sometimes (e.g. for larger features or refactorings) it might
be better to use branches. Make a new branch to work on each
of your tasks, and then push it to GitHub and create a **pull
request** once you have it done. The purpose of using
branches is to avoid messing up with the main branch.

#### How to use branch to collaborate

* Update your main branch using:

    ```
    $ git pull origin main
    ```

* Create a new branch using:

    ```
    $ git branch <TASK NAME>
    e.g. git branch new-feature-xyz
    ```

* Switch to the branch you just created using:

    ```
    $ git checkout <BRANCH NAME>
    e.g. git checkout new-feature-xyz
    ```

* After you complete the task, switch to your main branch
using:

    ```
    $ git checkout main
    ```

* Push your branch using:

    ```
    $ git push origin <BRANCH NAME>
    ```

* Go to GitHub and create a pull request. Wait for the pull-request to be reviewed and merge the branch to main.


## Coding conventions

Start reading our code and you'll get feeling how we work. We optimize for readability:

  * No tabs are used in source code.
  * We indent using four spaces (soft tabs).
  * We ALWAYS put spaces after list items and method
    parameters (e.g. `[1, 2, 3]`, not `[1,2,3]`), around
    operators (`x += 1`, not `x+=1`).
  * Maximum source line length should be between 80 and 120
    characters. Preferably less than 80 characters but never
    more than 120 characters.
  * Add comments so that others can read your code more
    easily.
  * Source code comments must be written using english
    language.
  * This is open source software. Consider the people
    who will read your code, and make it look nice and easy
    understandable for them.

Thanks,

The hBPF project
