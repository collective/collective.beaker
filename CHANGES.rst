Changelog for collective.beaker
===============================

1.0b4 (unreleased)
------------------

- Code cleanup: pep8, pyflakes, check-manifest.  [maurits]

- Moved code to https://github.com/collective/collective.beaker
  [maurits]

- Fix issue where cookie values are urlencoded by Zope
  but not decoded before passing to Beaker.
  [davisagli]


1.0b3 (2011-05-11)
------------------

- fixed spelling issue in setup.py
  [ajung]


1.0b2 (2010-01-23)
------------------

- Fix support for signed cookies (the ``secret`` parameter) in sessions.
  [optilude]

- Provide better testing tools and more resilient test setup.
  [optilude]

- Make the ZCML directive more resilient to configurations where there is
  no product_config. This can happen in test setup, for example.
  [optilude]


1.0b1 (2009-12-10)
------------------

- Initial release
  [optilude]
