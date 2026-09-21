# Security

This library is pinned by test beds that drive real network equipment. If
you find a contract or operation whose behaviour could damage a test bed
(an operation that writes where it documents a read, a default that
disables a safety check, a model that lets an unsafe value through the
type gate), report it privately rather than in a public issue: e-mail
rjvisser@alottabits.com with the symbol path, the affected version and a
description. You will get an acknowledgement within 7 days and a fix or a
stated plan within 30 days; the fix ships as the next PATCH release and
its changelog entry credits the reporter unless asked otherwise.
