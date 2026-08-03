/* AutomationVille - the practice shop under test.
 *
 * A look-alike of automationexercise.com, small enough to read in one
 * sitting. Two rules make it usable as a teaching target:
 *
 *  1. NO REAL TIMERS. Pyodide runs the learner's Python on this same
 *     thread, so a setTimeout callback could never fire while their test
 *     is running. Anything that "takes time" is queued on the virtual
 *     clock below, and only the Playwright shim's auto-wait loop moves
 *     it. Auto-waiting is therefore taught faithfully AND deterministically:
 *     the same test takes the same virtual milliseconds on every run.
 *
 *  2. THE DOM MATCHES THE REAL SITE. Same ids (#search_product,
 *     #susbcribe_email - yes, the real site's typo), same class names
 *     (.productinfo, .shop-menu, .cart_quantity), same headings. A
 *     solution written against this app works unchanged against
 *     automationexercise.com and against the kit's learn/ tests.
 */
(function () {
  "use strict";

  // ---------------------------------------------------------------- clock

  // The virtual clock. `after(ms, fn)` is our setTimeout; nothing runs
  // until somebody calls `advance()`.
  var clock = {
    now: 0,
    queue: [],
    seq: 0,
    latency: 1,                 // scenario knob: 2 = everything twice as slow
    after: function (ms, fn) {
      this.queue.push({ at: this.now + ms * this.latency, seq: this.seq++, fn: fn });
    },
    advance: function (ms) {
      var target = this.now + ms;
      for (;;) {
        // Re-scan every iteration: a due effect may queue another one.
        var due = this.queue.filter(function (e) { return e.at <= target; });
        if (!due.length) break;
        due.sort(function (a, b) { return a.at - b.at || a.seq - b.seq; });
        var next = due[0];
        this.queue.splice(this.queue.indexOf(next), 1);
        this.now = next.at;
        next.fn();
      }
      this.now = target;
      return this.now;
    },
    reset: function (latency) {
      this.now = 0; this.queue = []; this.seq = 0; this.latency = latency || 1;
    }
  };

  // ------------------------------------------------------------ catalogue

  // Eight products: enough to teach counts, filtering and .nth() without
  // making the preview panel scroll forever.
  var CATALOGUE = [
    { id: 1, name: "Blue Top", price: 500, category: "Women > Tops", brand: "Polo" },
    { id: 2, name: "Men Tshirt", price: 400, category: "Men > Tshirts", brand: "H&M" },
    { id: 3, name: "Sleeveless Dress", price: 1000, category: "Women > Dress", brand: "Madame" },
    { id: 4, name: "Stylish Dress", price: 1500, category: "Women > Dress", brand: "Madame" },
    { id: 5, name: "Winter Top", price: 600, category: "Women > Tops", brand: "Polo" },
    { id: 6, name: "Summer White Top", price: 400, category: "Women > Tops", brand: "H&M" },
    { id: 7, name: "Madame Top For Women", price: 1000, category: "Women > Tops", brand: "Madame" },
    { id: 8, name: "Fancy Green Top", price: 700, category: "Women > Tops", brand: "Polo" }
  ];

  var BASE_URL = "https://automationexercise.com";

  // ---------------------------------------------------------------- state

  var state;

  function freshState(scenario) {
    var s = {
      route: "/",
      // `query` is the search that has FINISHED (the box's own text lives
      // in forms.search_product, like a real uncontrolled input).
      query: null,
      searching: false,
      cart: [],                 // [{ id, qty }]
      accounts: {},             // email -> { name, password, details }
      user: null,               // { name, email }
      signupDraft: null,        // { name, email } between /login and /signup
      accountDeleted: false,
      loginError: false,
      signupError: null,
      subscribed: false,
      contactSent: false,
      orderPlaced: false,
      invoiceDownloaded: false,
      // Off by default: an overlay that swallows every click would turn
      // each lesson into the same lesson. Zone 1 switches it on for the
      // one challenge that is actually about dismissing it.
      consentOpen: false,
      cartModal: "closed",      // closed | opening | open | closing
      forms: {},                // every input's value, keyed by id or name
      viewing: null             // product id on /product_details/<id>
    };
    scenario = scenario || {};
    if (scenario.route) s.route = scenario.route;
    if (scenario.consent) s.consentOpen = true;
    if (scenario.cart) {
      scenario.cart.forEach(function (item) {
        s.cart.push({ id: item.id, qty: item.qty || 1 });
      });
    }
    if (scenario.account) {
      // Pre-register an account so login lessons need not sign up first.
      s.accounts[scenario.account.email] = {
        name: scenario.account.name,
        password: scenario.account.password,
        details: scenario.account.details || {}
      };
    }
    if (scenario.loggedInAs) {
      s.user = { name: scenario.loggedInAs.name, email: scenario.loggedInAs.email };
    }
    if (scenario.viewing) { s.viewing = scenario.viewing; }
    return s;
  }

  // ------------------------------------------------------------- helpers

  function esc(text) {
    return String(text)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function money(rupees) { return "Rs. " + rupees; }

  function product(id) {
    return CATALOGUE.filter(function (p) { return p.id === Number(id); })[0];
  }

  function field(key) {
    return state.forms[key] === undefined ? "" : state.forms[key];
  }

  function visibleProducts() {
    if (state.query === null) return CATALOGUE;
    var needle = state.query.toLowerCase();
    return CATALOGUE.filter(function (p) {
      // Matches the real site: the search looks at the category too, not
      // only the product name. Test Case 9 leans on this - it is why you
      // cannot assert that EVERY hit contains the search word.
      return (p.name + " " + p.category).toLowerCase().indexOf(needle) !== -1;
    });
  }

  function cartRows() {
    return state.cart.map(function (line) {
      var p = product(line.id);
      return { product: p, qty: line.qty, total: p.price * line.qty };
    });
  }

  // --------------------------------------------------------------- render

  function menu() {
    var links = [
      '<li><a href="/" data-route="/">Home</a></li>',
      '<li><a href="/products" data-route="/products">Products</a></li>',
      '<li><a href="/view_cart" data-route="/view_cart">Cart</a></li>'
    ];
    if (state.user) {
      links.push('<li><a href="/delete_account" data-route="/delete_account">Delete Account</a></li>');
      links.push('<li><a href="/logout" data-route="/logout">Logout</a></li>');
    } else {
      links.push('<li><a href="/login" data-route="/login">Signup / Login</a></li>');
    }
    links.push('<li><a href="/test_cases" data-route="/test_cases">Test Cases</a></li>');
    links.push('<li><a href="/contact_us" data-route="/contact_us">Contact us</a></li>');
    if (state.user) {
      links.push('<li class="user">Logged in as ' + esc(state.user.name) + "</li>");
    }
    return '<div class="header-middle"><a class="logo" href="/" data-route="/">Automation Exercise</a>' +
      '<div class="shop-menu"><ul class="nav">' + links.join("") + "</ul></div></div>";
  }

  function consent() {
    if (!state.consentOpen) return "";
    // A real overlay: it covers the page, so a click aimed at anything
    // underneath is intercepted. That is not decoration - it is the
    // lesson about actionability.
    return '<div class="consent-popup" id="consent-popup" role="dialog" aria-label="Consent">' +
      '<div class="consent-box"><p>We and our partners use cookies to personalise content.</p>' +
      '<button type="button" class="btn btn-primary" data-action="consent">Consent</button>' +
      "</div></div>";
  }

  function footer() {
    var message = state.subscribed
      ? '<div class="alert-success alert">You have been successfully subscribed!</div>'
      : "";
    return '<footer class="footer-widget"><h2>Subscription</h2>' + message +
      '<div class="searchform">' +
      '<input type="email" id="susbcribe_email" name="susbcribe_email" ' +
      'placeholder="Your email address" value="' + esc(field("susbcribe_email")) + '">' +
      '<button type="button" id="subscribe" data-action="subscribe" aria-label="Subscribe">&#8594;</button>' +
      "</div></footer>";
  }

  function cartModal() {
    if (state.cartModal === "closed") return "";
    // Hidden while it animates in or out - clicking it then would miss.
    var hidden = state.cartModal !== "open" ? ' style="display:none"' : "";
    return '<div class="modal-backdrop"></div>' +
      '<div class="modal" id="cartModal"' + hidden + ' role="dialog" aria-label="Add to cart">' +
      '<div class="modal-content"><h4 class="modal-title">Added!</h4>' +
      "<p>Your product has been added to cart.</p>" +
      '<p><a href="/view_cart" data-route="/view_cart">View Cart</a></p>' +
      '<button type="button" class="btn btn-success close-modal" data-action="close-modal">' +
      "Continue Shopping</button></div></div>";
  }

  function productGrid(items) {
    return '<div class="features_items">' + items.map(function (p) {
      return '<div class="col-sm-4"><div class="product-image-wrapper"><div class="single-products">' +
        '<div class="productinfo text-center">' +
        "<h2>" + money(p.price) + "</h2>" +
        "<p>" + esc(p.name) + "</p>" +
        '<a href="#" class="btn btn-default add-to-cart" data-action="add-to-cart" ' +
        'data-product-id="' + p.id + '">Add to cart</a></div>' +
        '<div class="choose"><ul class="nav nav-pills nav-justified"><li>' +
        '<a href="/product_details/' + p.id + '" data-route="/product_details/' + p.id + '">' +
        "View Product</a></li></ul></div></div></div></div>";
    }).join("") + "</div>";
  }

  var ROUTES = {};

  ROUTES["/"] = function () {
    return '<div class="carousel"><h1>AutomationVille</h1>' +
      "<p>Full-Fledged practice website for Automation Engineers</p>" +
      // The real site has this second "Test Cases" link as a big button
      // as well as the one in the menu - which is exactly why the kit's
      // Test Case 7 needs .first. Reproduced on purpose.
      '<a class="btn btn-primary test-cases-cta" href="/test_cases" ' +
      'data-route="/test_cases">Test Cases</a></div>' +
      '<h2 class="title text-center">Features Items</h2>' +
      productGrid(CATALOGUE.slice(0, 6));
  };

  ROUTES["/products"] = function () {
    var search = '<div class="search_box"><input type="text" id="search_product" name="search" ' +
      'placeholder="Search Product" value="' + esc(field("search_product")) + '">' +
      '<button type="button" id="submit_search" data-action="search" aria-label="Search">' +
      "&#128269;</button></div>";
    if (state.searching) {
      // Mid-request: the old results are gone and the new ones have not
      // arrived. A test that checks right now finds nothing - which is
      // exactly what auto-waiting is for.
      return search + '<p class="loading">Loading...</p>';
    }
    var heading = state.query === null ? "All Products" : "Searched Products";
    var items = visibleProducts();
    var empty = items.length ? "" : '<p class="no-results">No products matched your search.</p>';
    return search + '<h2 class="title text-center">' + heading + "</h2>" +
      empty + productGrid(items);
  };

  ROUTES["/product_details"] = function () {
    var p = product(state.viewing);
    if (!p) return "<h2>Product not found</h2>";
    return '<div class="product-information"><h2>' + esc(p.name) + "</h2>" +
      "<p>Category: " + esc(p.category) + "</p>" +
      "<span><span>" + money(p.price) + "</span>" +
      '<label for="quantity">Quantity:</label>' +
      '<input type="number" id="quantity" name="quantity" value="' +
      esc(field("quantity") || "1") + '" min="1">' +
      '<button type="button" class="btn btn-default cart" data-action="add-detail-to-cart" ' +
      'data-product-id="' + p.id + '">Add to cart</button></span>' +
      "<p><b>Availability:</b> In Stock</p>" +
      "<p><b>Brand:</b> " + esc(p.brand) + "</p></div>";
  };

  ROUTES["/view_cart"] = function () {
    var rows = cartRows();
    if (!rows.length) {
      return "<h2>Shopping Cart</h2>" +
        '<section id="empty_cart"><p class="text-center">Cart is empty! ' +
        '<a href="/products" data-route="/products">Click here</a> to buy products.</p></section>';
    }
    var body = rows.map(function (row) {
      return '<tr id="product-' + row.product.id + '">' +
        '<td class="cart_description"><h4><a href="/product_details/' + row.product.id +
        '" data-route="/product_details/' + row.product.id + '">' +
        esc(row.product.name) + "</a></h4></td>" +
        '<td class="cart_price"><p>' + money(row.product.price) + "</p></td>" +
        '<td class="cart_quantity"><button class="disabled" type="button">' + row.qty + "</button></td>" +
        '<td class="cart_total"><p class="cart_total_price">' + money(row.total) + "</p></td>" +
        '<td class="cart_delete"><a class="cart_quantity_delete" href="#" data-action="remove" ' +
        'data-product-id="' + row.product.id + '" aria-label="Remove ' + esc(row.product.name) +
        '">X</a></td></tr>';
    }).join("");
    var total = rows.reduce(function (sum, r) { return sum + r.total; }, 0);
    return "<h2>Shopping Cart</h2>" +
      '<table id="cart_info_table" class="table table-condensed"><thead><tr>' +
      "<td>Item</td><td>Price</td><td>Quantity</td><td>Total</td><td></td>" +
      "</tr></thead><tbody>" + body + "</tbody></table>" +
      '<p class="cart_grand_total">Total: ' + money(total) + "</p>" +
      '<a class="btn btn-default check_out" href="/checkout" data-route="/checkout">' +
      "Proceed To Checkout</a>";
  };

  ROUTES["/login"] = function () {
    var loginError = state.loginError
      ? '<p class="login-error">Your email or password is incorrect!</p>' : "";
    var signupError = state.signupError
      ? '<p class="signup-error">' + esc(state.signupError) + "</p>" : "";
    return '<div class="login-form"><h2>Login to your account</h2>' + loginError +
      '<form><label for="login-email">Email Address</label>' +
      '<input type="email" id="login-email" name="email" data-qa="login-email" ' +
      'placeholder="Email Address" value="' + esc(field("login-email")) + '">' +
      '<label for="login-password">Password</label>' +
      '<input type="password" id="login-password" name="password" data-qa="login-password" ' +
      'placeholder="Password" value="' + esc(field("login-password")) + '">' +
      '<button type="button" data-qa="login-button" data-action="login">Login</button></form></div>' +
      '<div class="signup-form"><h2>New User Signup!</h2>' + signupError +
      '<form><label for="signup-name">Name</label>' +
      '<input type="text" id="signup-name" name="name" data-qa="signup-name" ' +
      'placeholder="Name" value="' + esc(field("signup-name")) + '">' +
      '<label for="signup-email">Email Address</label>' +
      '<input type="email" id="signup-email" name="email" data-qa="signup-email" ' +
      'placeholder="Email Address" value="' + esc(field("signup-email")) + '">' +
      '<button type="button" data-qa="signup-button" data-action="signup">Signup</button>' +
      "</form></div>";
  };

  function textInput(id, label) {
    return '<label for="' + id + '">' + esc(label) + "</label>" +
      '<input type="text" id="' + id + '" name="' + id + '" data-qa="' + id +
      '" placeholder="' + esc(label) + '" value="' + esc(field(id)) + '">';
  }

  function selectField(id, label, options, selected) {
    var opts = options.map(function (o) {
      var value = typeof o === "string" ? o : o.value;
      var text = typeof o === "string" ? o : o.label;
      var mark = String(selected) === String(value) ? " selected" : "";
      return '<option value="' + esc(value) + '"' + mark + ">" + esc(text) + "</option>";
    }).join("");
    return '<label for="' + id + '">' + esc(label) + "</label>" +
      '<select id="' + id + '" name="' + id + '" data-qa="' + id + '">' +
      '<option value="">-- select --</option>' + opts + "</select>";
  }

  ROUTES["/signup"] = function () {
    if (!state.signupDraft) return "<h2>Start at Signup / Login</h2>";
    var days = [];
    for (var d = 1; d <= 31; d++) days.push(String(d));
    var monthNames = ["January", "February", "March", "April", "May", "June", "July",
      "August", "September", "October", "November", "December"];
    var months = monthNames.map(function (m, i) { return { value: String(i + 1), label: m }; });
    var years = [];
    for (var y = 1990; y <= 2005; y++) years.push(String(y));
    return '<div class="login-form"><h2>Enter Account Information</h2><form>' +
      '<label for="id_gender1"><input type="radio" id="id_gender1" name="id_gender" value="Mr"' +
      (field("id_gender") === "Mr" ? " checked" : "") + "> Mr.</label>" +
      '<label for="id_gender2"><input type="radio" id="id_gender2" name="id_gender" value="Mrs"' +
      (field("id_gender") === "Mrs" ? " checked" : "") + "> Mrs.</label>" +
      '<label for="name">Name</label>' +
      '<input type="text" id="name" name="name" data-qa="name" value="' +
      esc(state.signupDraft.name) + '" readonly>' +
      '<label for="password">Password</label>' +
      '<input type="password" id="password" name="password" data-qa="password" ' +
      'placeholder="Password" value="' + esc(field("password")) + '">' +
      selectField("days", "Date of Birth", days, field("days")) +
      selectField("months", "Month", months, field("months")) +
      selectField("years", "Year", years, field("years")) +
      '<label for="newsletter"><input type="checkbox" id="newsletter" name="newsletter"' +
      (field("newsletter") ? " checked" : "") + "> Sign up for our newsletter!</label>" +
      '<label for="optin"><input type="checkbox" id="optin" name="optin"' +
      (field("optin") ? " checked" : "") + "> Receive special offers from our partners!</label>" +
      "<h2>Address Information</h2>" +
      textInput("first_name", "First name") + textInput("last_name", "Last name") +
      textInput("company", "Company") + textInput("address", "Address") +
      textInput("address2", "Address 2") +
      selectField("country", "Country",
        ["United States", "Canada", "Australia", "India", "Israel", "New Zealand", "Singapore"],
        field("country")) +
      textInput("state", "State") + textInput("city", "City") +
      textInput("zipcode", "Zipcode") + textInput("mobile_number", "Mobile Number") +
      '<button type="button" data-qa="create-account" data-action="create-account">' +
      "Create Account</button></form></div>";
  };

  ROUTES["/account_created"] = function () {
    return '<h2 data-qa="account-created">Account Created!</h2>' +
      "<p>Congratulations! Your new account has been successfully created!</p>" +
      '<a class="btn btn-primary" data-qa="continue-button" href="/" ' +
      'data-action="continue-after-create">Continue</a>';
  };

  ROUTES["/delete_account"] = function () {
    return '<h2 data-qa="account-deleted">Account Deleted!</h2>' +
      "<p>Your account has been permanently deleted.</p>" +
      '<a class="btn btn-primary" data-qa="continue-button" href="/" data-route="/">Continue</a>';
  };

  ROUTES["/checkout"] = function () {
    if (!state.user) return "<h2>Please login to check out</h2>";
    var rows = cartRows();
    var lines = rows.map(function (r) {
      return "<li>" + esc(r.product.name) + " x " + r.qty + " = " + money(r.total) + "</li>";
    }).join("");
    var d = (state.accounts[state.user.email] || {}).details || {};
    return '<h2 class="heading">Address Details</h2>' +
      '<ul id="address_delivery" class="address">' +
      '<li class="address_title">Your delivery address</li>' +
      '<li class="address_firstname">' +
      esc(((d.first_name || "") + " " + (d.last_name || "")).trim()) + "</li>" +
      '<li class="address_company">' + esc(d.company || "") + "</li>" +
      '<li class="address_address1">' + esc(d.address || "") + "</li>" +
      '<li class="address_address2">' + esc(d.address2 || "") + "</li>" +
      '<li class="address_city">' +
      esc(((d.city || "") + " " + (d.state || "") + " " + (d.zipcode || "")).trim()) + "</li>" +
      '<li class="address_country_name">' + esc(d.country || "") + "</li>" +
      '<li class="address_phone">' + esc(d.mobile_number || "") + "</li></ul>" +
      '<h2 class="heading">Review Your Order</h2><ul class="order-review">' + lines + "</ul>" +
      '<label for="order-comment">Comment</label>' +
      '<textarea id="order-comment" name="message" placeholder="Add a comment">' +
      esc(field("order-comment")) + "</textarea>" +
      '<a class="btn btn-default check_out" href="/payment" data-route="/payment">Place Order</a>';
  };

  ROUTES["/payment"] = function () {
    if (state.orderPlaced) {
      var note = state.invoiceDownloaded
        ? '<p class="invoice-note">Invoice downloaded.</p>' : "";
      return '<h2 data-qa="order-placed">Congratulations! Your order has been confirmed!</h2>' +
        '<a class="btn btn-default check_out" href="/invoice" data-action="download-invoice">' +
        "Download Invoice</a>" + note;
    }
    return "<h2>Payment</h2><form>" +
      '<label for="name_on_card">Name on Card</label>' +
      '<input type="text" id="name_on_card" name="name_on_card" data-qa="name-on-card" ' +
      'placeholder="Name on Card" value="' + esc(field("name_on_card")) + '">' +
      '<label for="card_number">Card Number</label>' +
      '<input type="text" id="card_number" name="card_number" data-qa="card-number" ' +
      'placeholder="Card Number" value="' + esc(field("card_number")) + '">' +
      '<label for="cvc">CVC</label>' +
      '<input type="text" id="cvc" name="cvc" data-qa="cvc" placeholder="ex. 311" value="' +
      esc(field("cvc")) + '">' +
      '<label for="expiry_month">Expiration</label>' +
      '<input type="text" id="expiry_month" name="expiry_month" data-qa="expiry-month" ' +
      'placeholder="MM" value="' + esc(field("expiry_month")) + '">' +
      '<input type="text" id="expiry_year" name="expiry_year" data-qa="expiry-year" ' +
      'placeholder="YYYY" value="' + esc(field("expiry_year")) + '">' +
      '<button type="button" data-qa="pay-button" data-action="pay">Pay and Confirm Order</button>' +
      "</form>";
  };

  ROUTES["/contact_us"] = function () {
    if (state.contactSent) {
      return '<h2 class="title text-center">Contact Us</h2>' +
        '<div class="status alert alert-success">' +
        "Success! Your details have been submitted successfully.</div>" +
        '<a class="btn btn-success" href="/" data-route="/">Home</a>';
    }
    return '<h2 class="title text-center">Contact Us</h2><div class="contact-form">' +
      "<h2>Get In Touch</h2><form>" +
      '<label for="contact-name">Name</label>' +
      '<input type="text" id="contact-name" name="name" data-qa="name" placeholder="Name" ' +
      'value="' + esc(field("contact-name")) + '">' +
      '<label for="contact-email">Email</label>' +
      '<input type="email" id="contact-email" name="email" data-qa="email" placeholder="Email" ' +
      'value="' + esc(field("contact-email")) + '">' +
      '<label for="contact-subject">Subject</label>' +
      '<input type="text" id="contact-subject" name="subject" data-qa="subject" ' +
      'placeholder="Subject" value="' + esc(field("contact-subject")) + '">' +
      '<label for="contact-message">Your Message Here</label>' +
      '<textarea id="contact-message" name="message" data-qa="message" ' +
      'placeholder="Your Message Here">' + esc(field("contact-message")) + "</textarea>" +
      '<button type="button" data-qa="submit-button" data-action="contact-submit">Submit</button>' +
      "</form></div>";
  };

  ROUTES["/test_cases"] = function () {
    return '<h2 class="title text-center">Test Cases</h2>' +
      "<p>Below is the list of test Cases for practice.</p>" +
      '<ul class="panel-group"><li>Register User</li>' +
      "<li>Login User with correct email and password</li>" +
      "<li>Search Product</li><li>Add Products in Cart</li></ul>";
  };

  function render() {
    var key = state.route.indexOf("/product_details/") === 0 ? "/product_details" : state.route;
    var body = (ROUTES[key] || ROUTES["/"])();
    document.getElementById("app").innerHTML =
      menu() + '<main id="page">' + body + "</main>" + footer() + cartModal() + consent();
  }

  // --------------------------------------------------------------- actions

  function navigate(path) {
    state.route = path;
    if (path.indexOf("/product_details/") === 0) {
      state.viewing = path.split("/")[2];
      state.forms.quantity = "1";
    }
    // Leaving the products page ends any finished search, like a real reload.
    if (path !== "/products") { state.query = null; state.searching = false; }
    render();
  }

  function addToCart(id, qty) {
    var line = state.cart.filter(function (l) { return l.id === Number(id); })[0];
    if (line) line.qty += qty;
    else state.cart.push({ id: Number(id), qty: qty });
  }

  function openCartModal() {
    // Two-phase, like a real animated modal: it is in the DOM but hidden
    // for 300 virtual ms. Clicking it then would miss - which is exactly
    // why pages/products_page.py waits for it to be visible first.
    state.cartModal = "opening";
    render();
    clock.after(300, function () { state.cartModal = "open"; render(); });
  }

  var ACTIONS = {
    "consent": function () { state.consentOpen = false; render(); },

    "search": function () {
      var query = field("search_product");
      state.searching = true;
      state.query = null;
      render();
      clock.after(600, function () {
        state.searching = false;
        state.query = query;
        render();
      });
    },

    "add-to-cart": function (el) {
      addToCart(el.getAttribute("data-product-id"), 1);
      openCartModal();
    },

    "add-detail-to-cart": function (el) {
      var qty = parseInt(field("quantity") || "1", 10);
      addToCart(el.getAttribute("data-product-id"), isNaN(qty) ? 1 : qty);
      openCartModal();
    },

    "close-modal": function () {
      state.cartModal = "closing";
      render();
      clock.after(200, function () { state.cartModal = "closed"; render(); });
    },

    "remove": function (el) {
      var id = Number(el.getAttribute("data-product-id"));
      clock.after(300, function () {
        state.cart = state.cart.filter(function (l) { return l.id !== id; });
        render();
      });
    },

    "subscribe": function () {
      clock.after(500, function () {
        state.subscribed = true;
        state.forms.susbcribe_email = "";
        render();
      });
    },

    "login": function () {
      var email = field("login-email");
      var password = field("login-password");
      clock.after(500, function () {
        var account = state.accounts[email];
        if (account && account.password === password) {
          state.user = { name: account.name, email: email };
          state.loginError = false;
          state.forms["login-email"] = "";
          state.forms["login-password"] = "";
          navigate("/");
        } else {
          state.loginError = true;
          render();
        }
      });
    },

    "signup": function () {
      var name = field("signup-name");
      var email = field("signup-email");
      clock.after(400, function () {
        if (state.accounts[email]) {
          state.signupError = "Email Address already exist!";
          render();
          return;
        }
        state.signupError = null;
        state.signupDraft = { name: name, email: email };
        navigate("/signup");
      });
    },

    "create-account": function () {
      var draft = state.signupDraft;
      var details = {};
      ["first_name", "last_name", "company", "address", "address2", "country",
        "state", "city", "zipcode", "mobile_number"].forEach(function (key) {
          details[key] = field(key);
        });
      clock.after(700, function () {
        state.accounts[draft.email] = {
          name: draft.name, password: field("password"), details: details
        };
        navigate("/account_created");
      });
    },

    "continue-after-create": function () {
      state.user = { name: state.signupDraft.name, email: state.signupDraft.email };
      state.signupDraft = null;
      navigate("/");
    },

    "contact-submit": function () {
      clock.after(600, function () { state.contactSent = true; render(); });
    },

    "pay": function () {
      clock.after(800, function () {
        state.orderPlaced = true;
        state.cart = [];
        render();
      });
    },

    "download-invoice": function () {
      // A sandboxed iframe cannot download; record it so a test can still
      // assert that the click happened.
      state.invoiceDownloaded = true;
      render();
    }
  };

  function handleRoute(path) {
    if (path === "/logout") {
      state.user = null;
      navigate("/login");
      return;
    }
    if (path === "/delete_account") {
      if (state.user) {
        delete state.accounts[state.user.email];
        state.user = null;
        state.accountDeleted = true;
      }
      navigate("/delete_account");
      return;
    }
    navigate(path);
  }

  document.addEventListener("click", function (event) {
    var el = event.target.closest("[data-action], [data-route]");
    if (!el) return;
    event.preventDefault();
    var action = el.getAttribute("data-action");
    if (action && ACTIONS[action]) { ACTIONS[action](el); return; }
    var route = el.getAttribute("data-route");
    if (route) handleRoute(route);
  });

  // Keep every field's value in state so a re-render never loses what the
  // learner's script typed - and so expect(...).to_have_value() works.
  function remember(el) {
    if (el.type === "radio") { state.forms[el.name] = el.value; return; }
    var key = el.id || el.name;
    if (!key) return;
    state.forms[key] = el.type === "checkbox" ? el.checked : el.value;
  }
  document.addEventListener("input", function (event) { remember(event.target); });
  document.addEventListener("change", function (event) { remember(event.target); });

  // ------------------------------------------------------------ public API

  window.AV = {
    clock: clock,

    reset: function (scenario) {
      scenario = scenario || {};
      clock.reset(scenario.latency);
      state = freshState(scenario);
      render();
    },

    navigate: function (path) {
      // page.goto() is instant on purpose: latency belongs to the actions
      // the lessons are about, not to every single navigation.
      state.query = null;
      state.searching = false;
      handleRoute(path);
    },

    url: function () { return BASE_URL + state.route; },
    title: function () { return "Automation Exercise"; },

    // A plain-JSON view of the app, used to grade challenges on BEHAVIOUR
    // rather than on what the learner's source code looks like.
    snapshot: function () {
      return {
        route: state.route,
        url: BASE_URL + state.route,
        query: state.query,
        searching: state.searching,
        searchResults: state.query === null ? null : visibleProducts().length,
        cartCount: state.cart.length,
        cartUnits: state.cart.reduce(function (n, l) { return n + l.qty; }, 0),
        cartItems: cartRows().map(function (r) {
          return { name: r.product.name, qty: r.qty, price: r.product.price, total: r.total };
        }),
        user: state.user ? state.user.name : null,
        userEmail: state.user ? state.user.email : null,
        accounts: Object.keys(state.accounts),
        loginError: state.loginError,
        signupError: state.signupError,
        subscribed: state.subscribed,
        contactSent: state.contactSent,
        orderPlaced: state.orderPlaced,
        invoiceDownloaded: state.invoiceDownloaded,
        accountDeleted: state.accountDeleted,
        consentOpen: state.consentOpen,
        cartModal: state.cartModal,
        virtualMs: clock.now
      };
    }
  };

  window.AV.reset({});
})();
