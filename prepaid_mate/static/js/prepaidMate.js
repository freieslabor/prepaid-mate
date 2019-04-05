rfid_autofill = null;
credentials = {
	name: null,
	rfid: null,
	password: null,
}

function cleanUp() {
	// clear keypress handler
	$(document).off('keypress');

	// clear RFID autofill timer
	clearInterval(rfid_autofill);

	// hide current content of the page
	$('.view').hide();
}

function autoFillRFID() {
	// auto fill RFID code (last unknown code inserted)
	rfid_autofill = setInterval(function() {
		if ($('#createModifyRFID').val() == '') {
			$.get('/api/last_unknown_code', function(data) {
				if (data != '' && $('#createModifyRFID').val() == '') {
					$('#createModifyRFID').val(data);
				}
			});
		}
	}, 1000);
}

function showLogin() {
	$('#start').show();
	$('#InputUsername').focus();

	// login on enter keypress in form fields
	$('.loginfield').keypress(function(event) {
		if (event.which == 13) {
			login();
		}
	});
}

function login() {
	credentials.name = $('#InputUsername').val();
	credentials.password = md5($('#InputPassword').val());

	$.post( //pass login credentials to api
		'/api/account/view', credentials,
	).done( //on successful login call dashboard()
		function( accountData ) {
			var rfid = jQuery.parseJSON(accountData)[1];
			credentials.rfid = rfid;
			dashboard(accountData);
		}
	).fail( //on failed login attempt alert user and clear login inputs
		function( errorMessage ) {
			alert(errorMessage.responseText);
			$('#start').show();
			$('#InputUsername').val('');
			$('#InputPassword').val('');
		}
	);
}

function showNewAccount() {
	cleanUp();
	$('#newAccount').show();
	$('#createNewAccountButton').show();
	$('#modifyAccountButton').hide();
	$('#createModifyUsername').focus();

	// create account on enter keypress in create/modify form
	$('.createmodifyfield').keypress(function(event) {
		if (event.which == 13) {
			newAccount();
		}
	});

	autoFillRFID();
}

function newAccount(){
	var createCredentials = {
		name: null,
		code: null,
		password: null
	}

	createCredentials.name = $('#createModifyUsername').val();
	createCredentials.code = $('#createModifyRFID').val();
	createCredentials.password = md5($('#createModifyPassword').val());

	$.post( //pass login credentials to api
		'/api/account/create', createCredentials,
	).done( //on successful login call dashboard()
		function( accountData ) {
			cleanUp();
			showLogin();
		}
	).fail( //on failed login attempt alert user and clear login inputs
		function( errorMessage ) {
			alert(errorMessage.responseText);
			$('#createPassword').val('');
		}
	);
}

function dashboard(accountData) {
	cleanUp();
	$('#dashboard').show();
	var userName = jQuery.parseJSON(accountData)[0];
	$('#userNameDropdown').html(userName)
	getPaymentData();
	getCurrentBalance(accountData);
}

function showModifyAccount() {
	cleanUp();
	$('#modifyAccount').show();
	$('#createNewAccountButton').hide();
	$('#modifyAccountButton').show();

	$('#modifyUsername').val(credentials.name);
	$('#modifyRFID').val(credentials.rfid);

	autoFillRFID();
}

function modifyAccount() {
	var modifiedCredentials = {

		name: credentials.name,
		new_name: null,
		new_code: null,
		new_password: null,
		password: credentials.password
	}

	if(!$('#modifyPassword').val()) {
		alert('Password cannot be empty!');
		return;
	}

	modifiedCredentials.new_name = $('#modifyUsername').val();
	modifiedCredentials.new_code = $('#modifyRFID').val();
	modifiedCredentials.new_password = md5($('#modifyPassword').val());

	$.post( //pass login credentials to api
		'/api/account/modify', modifiedCredentials,
	).done( //on successful login call dashboard()
		function() {
			cleanUp();
			showLogin();
		}
	).fail( //on failed login attempt alert user and clear login inputs
		function( errorMessage ) {
			alert(errorMessage.responseText);
			$('#createPassword').val('');
		}
	);
}

function addBalance() {
	var balance = prompt('Aufladen:', '0.00');
	//Regex 1 or more digits / comma or dot / exactly 2 digits
	var regexBalance = new RegExp(/^(-?\d+((\,|\.)\d{2})?)$/);

	if (regexBalance.test(balance)) {
		balance = balance.replace(',', '.'); //balance can not contain ','
		var balanceData = {
			name: credentials.name,
			password: credentials.password,
			money: balance * 100 //money has to be in cents
		}

		$.post( //pass login credentials to api
			'/api/money/add', balanceData,
		).done( //on successful login call dashboard()
			function( transactionData ) {
				$('#transactionTableBody').empty();
				login();
			}
		).fail( //on failed login attempt alert user and clear login inputs
			function( errorMessage ) {
				alert(errorMessage.responseText);
				$('#start').show();
				$('#InputUsername').val('');
				$('#InputPassword').val('');
			}
		);
	} else {
		alert('Ungültiger Betrag!');
	}
}

function getCurrentBalance(accountData) {
	var currentBalance = jQuery.parseJSON(accountData);
	$('#userBalance').html(currentBalance[2] / 100 + '&euro;');
}

function getPaymentData() {
	$.post( //fetch transaction log from api
		'/api/money/view', credentials,
	).done(//fetched transactionData successfully
		function( transactionData ) {
			var transactions = jQuery.parseJSON(transactionData);
			for(var i = 0; i < transactions.length; i++) {
				//format unix time stamp to human readable format
				var dateTransaction = new Date(transactions[i][2]*1000).toLocaleDateString();
				dateTransaction += ' ' + new Date(transactions[i][2]*1000).toLocaleTimeString();

				var link = transactions[i][3] == '' ?
					'#' : 'https://www.codecheck.info/product.search?q=' + transactions[i][3];

				//convert cents to euro
				transactions[i][0] = transactions[i][0] / 100;
				//check if negative
				var amountClass = transactions[i][0] < 0 ? 'negativeAmount' : 'positiveAmount';
				//write '+' infront if positive
				if(transactions[i][0] > 0)
					transactions[i][0] = '+' + transactions[i][0];

				$('#transactionTableBody').append(
					$('<tr>')
				.append(
					$('<td>')
				.append(
					dateTransaction
				))
				.append(
					$('<td>')
				.append(
					'<a href="' + link + '">' + transactions[i][1] + '</a>'
				))
				.append(
					$('<td>')
				.append(
					transactions[i][0] + '&euro;'
				).addClass(amountClass)));
			}
		}
	).fail(//show error message from api
		function( errorMessage ) {
			alert(errorMessage.responseText);
		}
	);
}

// start here
showLogin();
