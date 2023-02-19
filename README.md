# ticgithub

*Tools to use a GitHub repository as a support ticket system.*

We had a shared inbox that didn't get a lot of traffic (not enough to justify
spending \$\$\$\$ on email ticketing solutions), but it was essential that all
emails that came in there get a timely response.

Essentially, our needs were:

* The ability to assign an email to an individual, and to notify that person
  that they have been assigned.
* The ability to see, at a glance, what emails were missing assignment.
* Some automation to ensure that we're reminded of any unassigned emails.
* Some automation to ensure that tickets are being closed in a timely fashion
  once they've been assigned.

The solution proposed here is to use GitHub issues (in a private repository) as
the ticket management system. This allows assignment and notifications as
normal on GitHub. GitHub Actions workflows are used to check email and post any
new email as issues, and to ping the team if issues haven't been
closed/assigned.

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

1. Enable IMAP the for GMail account associated with your inbox.
2. Turn on two-factor authentication for that GMail account.
3. Add an app password. Use a custom name; the value of the name does name
   matter (e.g, you can use "ticgithub" or "Support Repository" or anything
   else you want). Record that password; you will need to add it as a GitHub
   secret later.
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
3. Create the bot's personal access token (PAT), giving access to the
   repository. This will need to be done from within the bot's GitHub account.
4. Add the secrets to the GitHub repository. The names of the secrets are
   customizable, and will be the inputs to the configuration file, but you will
   need a secret to store each of:

   * the app password for your inbox
   * the password for your bot's SMTP account (if using sendmail functionality)
   * the bot's PAT with write access to the repository

## Configuration

`ticgithub` is configured with a YAML file stored at `.ticgithub.yml` in the
root directory of your issues repository. This file consists of two main groups
of settings: `config`, which defines the inbox, bot, and your team, and
`workflows`, which provides specific 

### Inbox configuration

### Bot configuration

### Team configuration

### Workflow configuration

Each workflow is a key within `workflows`. The name of the key must match the
name of the workflow. Detailed configuration for existing workflows is
described below. However, all workflows have the following parameters:

* `active`: Boolean determining whether or not the workflow is active. If the
  workflow is listed in the configuration and `active` is not explicitly
  listed, it is assumed that `active == true`.
* `dry`: Boolean determining whether to do a dry run. 

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


## Supported workflows in detail

### `emails-to-issues`

This is the main workflow that 

Complete and commented config example:

```yaml
```

### `unassigned-reminder`

### `unclosed-reminder`

### `assignment-to-gmail`

This workflow is triggered immediately when an issue is assigned.
