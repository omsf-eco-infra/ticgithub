# ticgithub

*Tools to use a GitHub repository as a support ticket system.*

We had a shared inbox that didn't get a lot of traffic (not enough to justify
spending \$<!-- -->\$\$<!-- -->\$ on email ticketing solutions), but it was
essential that all emails that came in there get a timely response.

Essentially, our needs were:

* The ability to assign an email to an individual, and to notify that person
  that they have been assigned.
* The ability to see, at a glance, what emails were missing assignment.
* Some automation to ensure that we're reminded of any unassigned emails.
* Some automation to ensure that tickets are being closed in a timely fashion
  once they've been assigned.

The solution proposed here is to use GitHub issues as the ticket management
system. This allows assignment and notifications as normal on GitHub. GitHub
Actions workflows are used to check email and post any new email as issues, and
to ping the team if issues haven't been closed/assigned.

## Setup

**Ingredients:**

* An **inbox** where you receive support emails. Currently must be GMail.
* A **bot** which consists of a GitHub user account and (optionally) an SMTP
  account.
* A **repository** to host your support tickets.

### Inbox setup

Some current workflows make use of some GMail-specific IMAP extensions
(specifically, labels), and therefore only GMail is fully supported.

To use your existing GMail account, you will need to provide an app password,
which currently requires enabling two-factor authentication. You will also need
to enable IMAP in your account. In detail:

1. [Enable IMAP](https://support.google.com/a/answer/105694) the for GMail
   account associated with your inbox.
2. [Turn on two-factor
   authentication](https://support.google.com/accounts/answer/185839) for that
   Google account.
3. [Add an app password](https://support.google.com/accounts/answer/185833).
   Use a custom name; the value of the name does name matter (e.g, you can use
   "ticgithub" or "Support Repository" or anything else you want). Record that
   password; you will need to add it as a GitHub secret later.
4. Create labels in your account to represent assignment. I recommend nested
   labels under the `assigned` label, e.g., `assigned/dwhswenson`.

### Bot setup

The bot consists of an optional SMTP account and a GitHub user account. The
bot's SMTP account is used to send emails to the team (e.g., to reply in-thread
to provide a link to the relevant GitHub issue). It is probably logical in most
cases for the bot to have its own email address, and for that to be the email
address used to register the bot's GitHub account.

You will need to:

1. Create an email account for the bot. If using GMail, you will have to go
   through the steps of setting up an app password as described under "Inbox
   setup."
2. Create a GitHub account for the bot.

After you have created the repository (see below), you will also need to create
a personal access token with 

### Repository setup

This is just a standard GitHub repository. Current approach assumes that all
issues are support tickets that should be managed by the bot (with reminders,
etc.) so at this stage it is recommended that this repository be kept separate
from the core development repository. The repository can be private, although
the usage of `ticgithub` workflows will subtract from your allotted GitHub
Actions minutes for the month.

To set up the repository:

1. Create the repository.
2. Give your bot write access to the repository.
3. Create the bot's [personal access token
   (PAT)](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token),
   giving access to the repository. This will need to be done from within the
   bot's GitHub account.
4. [Add the
   secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
   to the GitHub repository. The names of the secrets are customizable, and
   will be the inputs to the configuration file, but you will
   need a secret to store each of:

   * the app password for your inbox
   * the password for your bot's SMTP account (if using sendmail functionality)
   * the bot's PAT with write access to the repository

## Configuration

`ticgithub` is configured with a YAML file stored at `.ticgithub.yml` in the
root directory of your issues repository. This file consists of two main groups
of settings: `config`, which defines the inbox, bot, and your team, and
`workflows`, which provides specific instructions for the workflows that are
installed with the `python -m ticgithub.build` command.

### Inbox configuration

The inbox is the mailbox that you want to turn into GitHub issues. It has the
following entries:

* `type`: currently, must be `gmail`
* `user`: the username, e.g., `inboxaddress@gmail.com`
* `secret`: the name of the GitHub secret containing the app password
* `host`: for gmail, `imap.gmail.com`

### Bot configuration

The bot performs the actions of writing to the repository and sending emails
back shared inbox to link to new repository issues. As such, you must define
both a GitHub user for the bot and a sendmail user for the bot. If you do not
use the sendmail functionality (`reply-inbox: active: false`) *you still must
define the sendmail information* but it need not be valid. For example, you can
use `user: foo` and `secret: not_registered_in_github`.

* `token_name`: name of the GitHub secret containing the bot's PAT (possibly
  restricted to a single repo)
* `repo`: full name (`owner/repository`) for the repository this bot should be
  managing.
* `sendmail`: sendmail user info, containing of a dict with the following:
  * `user`: sendmail username, e.g., `botaddress@gmail.com`
  * `secret`: name of the GitHub secret containing the sendmail password
  * `host`: sendmail hostname, e.g., `smtp.gmail.com`


### Team configuration

The `team` parameter under `config` is a list of team members. Each team member
should have the following keys:

* `github`: GitHub username, e.g., `dwhswenson`
* `email`: sufficient part of the email to uniquely identify the user (doesn't
  have to be the full email), e.g., `david.swenson`
* `label`: label creating in the Gmail inbox to indicate that this user has
  been assigned, e.g., `assigned/dwhswenson`

## Workflow configuration

Each workflow is a key within `workflows` in the `.ticgithub.yml`.  The name of
the key must match the name of the workflow. 

* `active`: Boolean determining whether or not the workflow is active. If the
  workflow is listed in the configuration and `active` is not explicitly
  listed, it is assumed that `active == true`.
* `dry`: Boolean determining whether to do a dry run. Default `false`

### `emails-to-issues`

This is the workflow that converts your inbox into GitHub issues. 
It is a scheduled workflow, but can also be [run
manually](https://docs.github.com/en/actions/managing-workflow-runs/manually-running-a-workflow)
using the `workflow_dispatch` event.

Its parameters are:

* `active`: Boolean determining whether or not the workflow is active. If the
  workflow is listed in the configuration and `active` is not explicitly
  listed, it is assumed that `active == true`.
* `dry`: Boolean determining whether to do a dry run. Default `false`
* `cron`: crontab entry for when this workflow should be run
* `filters`: list of filters to exclude emails from creating issues, options
  are:
  * bot filter: filters out emails send from the bot's sendmail address
    * `name: bot`
    * `active`: whether to use the filter; default `true`
  * team filter: whether to filter emails from the team but not directly to
    (i.e., CC'd, BCC'd to) the inbox
    * `name: team`
    * `active`: whether to use the filter; default `true`
  * omitted senders filter: filter emails that include specific strings
    * `name: omit-senders`
    * `active`: whether to use the filter; default `true`
    * `senders`: list of strings; any sender that matches this string will not
      generate an issue
  * `recent`: time delta indicating how recently (rounded down to the day)
    emails should be loaded.
    Parameters match those of `datetime.timedelta` (i.e., `days`, `hours`,
    `minutes`, `seconds`, ...)
  * `reply-inbox`: parameters for sending a reply to the inbox to indicate that
    a GitHub issue has been created for this email
    * `active`: whether to send the email; default `true`
    * `template`: a file in the `string.Template` format for the reply email.
      Allowed keys:
      * `$GITHUB_URL`: the URL for the issue

### `unassigned-reminder`

This workflow posts a comment to remind that an open issue has remained
unassigned after some period of time.
It is a scheduled workflow, but can also be [run
manually](https://docs.github.com/en/actions/managing-workflow-runs/manually-running-a-workflow)
using the `workflow_dispatch` event.

Its parameters are:

* `active`: Boolean determining whether or not the workflow is active. If the
  workflow is listed in the configuration and `active` is not explicitly
  listed, it is assumed that `active == true`.
* `dry`: Boolean determining whether to do a dry run. Default `false`
* `cron`: crontab entry for when this workflow should be run
* `email-ticket-only`: whether to only comment on issues that appear to have
  been created from by the `emails-to-issues` task.
* `delay`: time delta, any issues without assignment that have been open for
  longer than this time will trigger a reminder comment.
  Parameters match those of `datetime.timedelta` (i.e., `days`, `hours`,
  `minutes`, `seconds`, ...)
* `template`: a file in the `string.Template` format for the reply email.
  Allowed keys: (none yet)
* `notify`: list of additional GitHub user/team names (without the `@`) to
  `@`-mention in the comment

### `unclosed-reminder`

This workflow posts a comment to remind that an assigned issue hasn't been
closed after some period of time.
It is a scheduled workflow, but can also be [run
manually](https://docs.github.com/en/actions/managing-workflow-runs/manually-running-a-workflow)
using the `workflow_dispatch` event.

Its parameters are:

* `active`: Boolean determining whether or not the workflow is active. If the
  workflow is listed in the configuration and `active` is not explicitly
  listed, it is assumed that `active == true`.
* `dry`: Boolean determining whether to do a dry run. Default `false`
* `cron`: crontab entry for when this workflow should be run
* `email-ticket-only`: whether to only comment on issues that appear to have
  been created from by the `emails-to-issues` task.
* `delay`: time delta, any issues still open with the last assignment event
  older than this time will trigger a reminder comment.
  Parameters match those of `datetime.timedelta` (i.e., `days`, `hours`,
  `minutes`, `seconds`, ...)
* `template`: a file in the `string.Template` format for the reply email.
  Allowed keys: (none yet)
* `notify`: list of additional GitHub user/team names (without the `@`) to
  `@`-mention in the comment


### `assignment-to-gmail`

This workflow is triggered immediately when an issue is assigned.

Its parameters are:

* `active`: Boolean determining whether or not the workflow is active. If the
  workflow is listed in the configuration and `active` is not explicitly
  listed, it is assumed that `active == true`.
* `dry`: Boolean determining whether to do a dry run. Default `false`

### Build-time vs. run-time configuration

Some parameters are used during the `ticgithub.build` process to create the GHA
workflows. These parameters are build-time parameters. Others are used from
within the workflow run. These are run-time parameters.

If changing build-time parameters, you will need to rerun the `ticgithub.build`
process. If unsure, rerunning `ticgithub.build` will never cause problems, and
might update your workflows for new changes.

Most parameters are run-time parameters. The exceptions are:

* Changes to the name of a `secret` (in `config`) will always be a build-time
  parameter.
* For scheduled workflows, changes to the `cron` schedule will always be a
  build-time parameter.

## "Installation" / Usage

Once you have created your `.ticgithub.yml` file, you can use `ticgithub` to
create the GHA workflows based on your configuration. On your local machine, in
a clone of your issues repository, install `ticgithub` into the current
environment:

```bash
python -m pip install ticgithub
```

From the root directory of your clone of the issues repository, run the command:

```bash
python -m ticgithub.build
```

This will create the relevant workflows. Ensure that they are added in a git
commit and push up to your default branch, and you'll have `ticgithub` up and
running!

## Running tasks locally

You can run any of the built-in tasks locally as well. To do this, use, e.g., 

```bash
python -m ticgithub.tasks.emails_to_issues
```

You will need to have environment variables set for your GitHub Actions secrets. To do this temporarily on the command line, just preface the command by setting the variables temporarily:

```bash
INBOX_PASSWORD="password" SENDMAIL_PASSWORD="password" BOT_TOKEN="token" python -m ticgithub.tasks.emails_to_issues
```

You can select choose a dry run by passing `--dry`. You can select a specific
configuration file (other than `./.ticgithub.yml`) with `--config` or `-c`.

The `assignment-to-gmail` task takes an additional parameter for the issue
number, e.g,

```bash
python -m ticgithub.tasks.assignment_to_gmail --dry 99
```

## Customizing the build process

The build process can be further customized based on a build config YAML file.
The default build config is at
[ticgithub/data/build_config.yml](https://github.com/dwhswenson/ticgithub/blob/main/ticgithub/data/build_config.yml).
This allows customization of the files generated by the `build` command. There
are two categories of customization: customization of `ticgithub` itself, and
customization of the individual workflows, under the `builders` heading.

Under the `ticgithub` heading:

* `install`: the command to run to install ticgithub
* `suffix`: a suffix (to distinguish multiple copies of the same workflow)
* `force-dry`: require all commands to run with the `--dry` flag
* `install-path`: path to install the GitHub Actions Workflows

The `builders` heading contains a list where each item is a workflow. For each
workflow, the following keys should be included:

* `config-name`: workflow name as used in configuration
* `run-command`: the command to run for this workflow
* `template`: the template file to use for this workflow; default is to first
  check if the provided value is a path that exists and if not, to check in
  `ticgithub/data/workflows/`
* `build-params`: build-time parameters from the main config for this workflow.
  These are key-value pairs with the name of the parameter in the config file
  as the key and the substitution variable from the template file (without the
  initial `$`) as the value.
