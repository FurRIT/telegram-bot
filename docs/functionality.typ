#import "@preview/cheq:0.2.3": checklist

#show: checklist
#show link: underline

#set heading(numbering: "1.")
#outline()

#let cite

#let fileref(path, ..args) = {
  let line = args.at(0, default: none)

  let lref = ""
  if line != none {
    lref = "#L" + str(line)
  }

  let url = (
    "https://github.com/FurRIT/oldBot/blob/1d7dc89001abf1e266092e610556a4de0d169b06/"
      + path
      + lref
  )
  let txt = path + lref
  link(url, txt)
}

= Overview

This document seeks to describe the behavior of the old Telegram bot (found in
the old bot repository #footnote[See
  #link("https://github.com/FurRIT/oldBot")]).

The behavior described was derived from a reading of the source code against
commit `1d7dc89001abf1e266092e610556a4de0d169b06`.

== Conventions

The source code for the bot has several repeated patterns. To improve the
readability of behavioral descriptions, some conventions are established as
textual shorthands for these patterns.

=== Messages

The bot often pulls static messages stored as HTML files from the `messages/`
directory #footnote[See
  #link("https://github.com/FurRIT/oldBot/tree/main/messages")]. Whenever a
behavioral description refers to a message (e.g. 'the `minecraft` message'),
a file of the same name is in the `messages` directory postfixed with
`.html`.

=== Approved Sender

The bot often performs a check for an approved sender #footnote[See the
  `checkIfApprovedSender` function in `bot.js`
  #link("https://github.com/FurRIT/oldBot/blob/main/bot.js")], which ensures that
the message being processed is either a private message from an administrator,
or a message from an approved chat.

The approved chats are stored in the
#link("https://github.com/FurRIT/oldBot/blob/1d7dc89001abf1e266092e610556a4de0d169b06/bot.js#L63")[`bot.APPROVED_CHATS`
  constant]; the approved administrators are stored in the
#link("https://github.com/FurRIT/oldBot/blob/1d7dc89001abf1e266092e610556a4de0d169b06/bot.js#L26")[`bot.FURRIT_ADMINS`
  constant].

Approved sender is a misnomer - the function is better described as checking if
some message source is approved.

Whenever this check is described it will be described as 'checking the message
source'.

#pagebreak()
= Processes

Some processes are accessed in multiple places - perhaps automatically or via
commands. This document exists to describe those processes to prevent duplicate
descriptions in the feature set section.

== Fining <process-fining>

Most of the fining functionality is defined in the `processAwooFine` function
(see #fileref("awoo_module/awoo.js", 33)).

+ A user is added to the database if they don't already exist
  (see #fileref("awoo_module/awoo.js", 36)).
+ The fine value is automatically created if it does not exist for a user, and
  incremented (see #fileref("awoo_module/awoo.js", 58), and
  #fileref("awoo_module/models/AwooFine.js", 33)).
+ The offending message is replied to with the new fine value (see
  #fileref("awoo_module/awoo.js", 132)).

=== April Fools

There is an additional check for whether or not the current date is april fools
day. If that is the case then,

- Instead of a value of 350, a random value in the range $[-4 dot 350, 4 dot
    350]$ is chosen (see #fileref("awoo_module/awoo.js", 51)).
- Users can be 'muzzled' (muted) for a period of time for awooing too much (see
  #fileref("awoo_module/awoo.js", 65)).

=== Notable Invariants

A User's AwooFine value can never be less than zero (see
#fileref("awoo_module/models/AwooFine.js", 48)).

== Bulletin <process-bulletin>

Bulletins are short messages intended to be sent on a weekly basis. They are
stored in the bulletins subdirectory of the messages directory (see
#fileref("messages/bulletins")).

== Events <process-events>

Events are one of the most complex processes because they rely on communication
between the FurRIT server.

The bot creates an HTTP server (see #fileref("server.js")) that receives
requests from the FurRIT webserver. To see OpenAPI documentation on the exposed
API surface, see @appendix-openapi.

Request parsing happens in the afformentioned server code. After information is
parsed it is passed into Telegram-specific handling code in
#fileref("events_module/event_new.js").


#pagebreak()
= Feature Set

Instead of attempting to describe the behavior of the original source code
wholesale, the description of its behavior is broken down into functional
pieces roughly corresponding to function definitions in the original source
code.

Each function is represented by one or more features. Features are listed
roughly in the order that they appear in the GitHub source tree. Each feature
has a tagline - coupled with a description of the current behavior of the
implementation.

#v(1em)

#let feature(text, content) = {
  block(
    breakable: false,
    [- [ ] #text]
      + content
      + line(length: 100%, stroke: (dash: "dashed"))
      + v(1.25em),
  )
}

#feature("Automatic Join Message - Art Channel")[
  When a new user joins the art chat the `artChatHeader`, `artChatRules`, and
  `artChatTags` messages are automatically sent.

  The bot will also repeat the same message when `/welcome` is used.

  See #fileref("art_chat_module/artChat.js", 5)
]

#feature("Welcome Command - Art Channel")[
  See above.

  See #fileref("art_chat_module/artChat.js", 5)
]

#feature("Rules - Art Channel")[
  When `/rules` is used the bot will repeat the `artChatRules` message.

  See #fileref("art_chat_module/artChat.js", 24)
]

#feature("Rules - Art Channel")[
  When `/tags` is used the bot will repeat the `artChatTags` message.

  See #fileref("art_chat_module/artChat.js", 36)
]

#feature("Automatic Awoo Fining")[
  After the message source is checked, a message is checked for whether or not
  it matches an 'awoo' regex - if so a user is automatically fined.

  See @process-fining for more information on fining.

  See #fileref("awoo_module/awoo.js", 11)
]

#feature("Fine Command")[
  The message sender is checked for administrator status; if the check passes
  the user that sent the message being replied to is fined.

  See @process-fining for more information on fining.

  See #fileref("awoo_module/awoo.js", 24)
]

#feature("AwooFines Command")[
  The message source is checked. Then, the message is scanned for a username
  search query.

  If a username from the search query exists, the database is searched for a
  quote sent by that user; otherwise a quote from the message sender is
  searched for.

  See #fileref("awoo_module/awoo.js", 135)
]

#feature("Pan Command")[
  The message source is checked. The message is then further checked to make
  sure that it is not: a forwarded message, from a bot, or a reply to oneself.

  Finally, the message being responded to is responded to with a pan sticker
  (see #fileref("ban_module/ban.js", 94)).

  See #fileref("ban_module/ban.js", 22)
]

#feature("Ban Command")[
  The message source is checked. The message is then further checked to make
  sure that it is not: a forwarded message, from a bot, or a reply to oneself.

  The bot then checks that the source of the message is an administrator.

  The bot revokes the following permissions from the original message sender:
  sending messages, sending media messages, sending other messages, adding web
  page previews. These permissions are revoked for one minute.

  To ensure that the permissions are restored a background task is scheduled to
  trigger after 70,000 MS (70 seconds).

  A random quirky message is sent as a reply when a user is banned (see
  #fileref("ban_module/ban.js", 3)).

  See #fileref("ban_module/ban.js", 22)
]

#feature("Bulletin Command")[
  The message source is checked. Then the bot sends the latest weekly bulletin.

  See @process-bulletin for more information on bulletins.

  See #fileref("bulletin_module/bulletin.js", 22)
]

#feature("Automatic Weekly Bulletin")[
  The bot is configured to automatically send a weekly bulletin, then pin that
  message in the chat.

  See @process-bulletin for more information on bulletins.

  See #fileref("bulletin_module/bulletin.js", 30)
]

#feature("Events")[
  Events are an relatively complex topic because they involve communication
  with a front-end server.

  For more information on events, see @process-events.
]

#feature("Rules - Forum Channel")[
  The message chat identifier is checked, then a message stored in the module
  is sent.

  See #fileref("forum_module/commands.js", 9)
]

#feature("Administrator Summons")[
  The message source is checked. Then, the message is forwarded to the
  administrators channel.

  See #fileref("main_module/main.js", 10)
]

#feature("Automatic Welcome Message - Main, AD, ROOVille, FurRITForum")[
  The join notification chat identifier is checked to make sure it is the main
  chat.

  Then, a welcome message is sent in the chat for the new member.

  See #fileref("main_module/main.js", 37)
]

#feature("Member Leave Message")[
  The message chat identifier is checked to make sure it is the main chat.

  Then, a message is sent notifying the chat that a user has left.

  See #fileref("main_module/main.js", 57)
]

#feature("Welcome Command - AD, ROOVille, FurRITForum")[
  The message source is checked. Then a message is sent for the appropriate
  chat.

  See #fileref("main_module/main.js", 66)
]

#feature("Rules - AD, ROOVille, FurRITForum")[
  The message source is checked. Then a message is sent for the appropriate
  chat.

  See #fileref("main_module/main.js", 66)
]

#feature("Links Command")[
  The message source is checked. Then the message `links` is sent.

  See #fileref("main_module/main.js", 94)
]

#feature("Channels SFW Command")[
  The message source is checked. Then the message `links_affiliated_sfw` is
  sent.

  See #fileref("main_module/main.js", 102)
]

#feature("Channels NSFW Command")[
  The message source is checked. Then the message `links_affiliated_nsfw` is
  sent.

  See #fileref("main_module/main.js", 109)
]

#feature("Commands Command")[
  The message source is checked. Then the message `commands` is sent.

  See #fileref("main_module/main.js", 117)
]


#feature("Automatic Timed Messages")[
  Three timed messages are scheduled to be sent,

  + The letters `e`, `f` or `a` to the ROOVille chat \@ 06:21 and 18:21

    See #fileref("main_module/main.js", 180)

  + The letter `e` to the main chat \@ 09:26 and 21:26

    See #fileref("main_module/main.js", 195)

  + The emoticon #emoji.tree.deciduous to the main chat \@ 04:20 and 16:20

    See #fileref("main_module/main.js", 204)
]

#feature("Quote Statistics")[
  The message source is checked. Then, the command issuer's message is checked
  for a reference to a username; if one is found the user it references is used
  to collect statistics, otherwise the command issuer is used.

  The database is queried to collect how many times the user being inspected,
  - Was quoted by other people
  - Authored quotes
]



#pagebreak()
= Appendix

== OpenAPI <appendix-openapi>

#raw(read("openapi.yaml"), lang: "yaml")
