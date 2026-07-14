# pages/ — the Page Object Model (POM)
#
# Each file in this folder describes ONE page of your app as a Python
# class: where things are on that page (locators) and what a user can do
# there (methods). Tests and helpers then talk in user language
# ("login_page.login(...)") instead of raw selectors.
#
# When your app changes, you fix the locator in ONE page class instead
# of in every test that used it.
#
# Add an import line here for each page class you create, so tests can
# write short imports like:  from pages import LoginPage

from pages.base_page import BasePage
