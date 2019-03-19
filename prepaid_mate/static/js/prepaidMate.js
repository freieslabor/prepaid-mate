$('#start').show();
$('#InputUsername').focus();

// login on enter keypress
$(document).keypress(function(event) {
	if (event.which == 13) {
		login();
    }
});

function newAccount() {
	$('.view').hide();
	$('#newAccount').show();
	$('#createNewAccountButton').show();
	$('#modifyAccountButton').hide();

	setInterval(function() {
		if ($('#createModifyRFID').val() == "") {
			$.get("/api/last_unknown_code", function(data) {
				if (data != "" && $('#createModifyRFID').val() == "") {
					$('#createModifyRFID').val(data);
				}
			});
		}
	}, 1000);
}

function createNewAccount(){
	var createCredentials = {
		name: null,
		code: null,
		password: null
	}

	createCredentials.name = $('#createUsername').val();
	createCredentials.code = $('#createRFID').val();
	createCredentials.password = $('#createPassword').val();

	$.post( //pass login credentials to api
		"/api/account/create", createCredentials,
	).done( //on successful login call dashboard()
		function( accountData ) {
			$('.view').hide();
			$('#start').show();
			$('#InputUsername').focus();
		}
	).fail( //on failed login attempt alert user and clear login inputs
		function( errorMessage ) {
			alert(errorMessage.responseText);
			$('#createPassword').val("");
		}
	);
}

credentials = {
	name: null,
	rfid: null,
	password: null,
}

function login() {
	credentials.name = $('#InputUsername').val();
	credentials.password = $('#InputPassword').val();

	$.post( //pass login credentials to api
		"/api/account/view", credentials,
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
			$('#InputUsername').val("");
			$('#InputPassword').val("");
		}
	);
}

function dashboard(accountData) {
	$('.view').hide();
	$('#dashboard').show();
	var userName = jQuery.parseJSON(accountData)[0];
	$('#userName').html(userName)
	getPaymentData();
	getCurrentBalance(accountData);
}

function showModifyUser() {
	$('.view').hide();
	$('#modifyAccount').show();
	$('#createNewAccountButton').hide();
  $('#modifyAccountButton').show();

	$('#modifyUsername').val(credentials.name);
	$('#modifyRFID').val(credentials.rfid);


}

function modifyUser() {
	//write credentials back to api
	credentials.name = $('#modifyUsername').val();
	credentials.rfid = $('#modifyRFID').val();
	credentials.password = $('#modifyPassword').val();
}

function addBalance() {
	var balance = prompt("Aufladen:", "0.00");
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
			"/api/money/add", balanceData,
		).done( //on successful login call dashboard()
			function( transactionData ) {
				$('#transactionTableBody').empty();
				login();
			}
		).fail( //on failed login attempt alert user and clear login inputs
			function( errorMessage ) {
				alert(errorMessage.responseText);
				$('#start').show();
				$('#InputUsername').val("");
				$('#InputPassword').val("");
			}
		);
	} else {
		alert('Ungültiger Betrag!');
	}
}

function getCurrentBalance(accountData) {
	var currentBalance = jQuery.parseJSON(accountData);
	$('#userBalance').html(currentBalance[2] / 100 + "&euro;");
}

function getPaymentData() {
	$.post( //fetch transaction log from api
		"/api/money/view", credentials,
	).done(//fetched transactionData successfully
		function( transactionData ) {
			var transactions = jQuery.parseJSON(transactionData);
			for(var i = 0; i < transactions.length; i++) {
				//format unix time stamp to human readable format
				var dateTransaction = new Date(transactions[i][2]*1000).toLocaleDateString();
				dateTransaction += " " + new Date(transactions[i][2]*1000).toLocaleTimeString();

				var link = transactions[i][3] == "" ?
					"#" : "https://www.codecheck.info/product.search?q=" + transactions[i][3];

				//convert cents to euro
				transactions[i][0] = transactions[i][0] / 100;
				//check if negative
				var amountClass = transactions[i][0] < 0 ? "negativeAmount" : "positiveAmount";
				//write '+' infront if positive
				if(transactions[i][0] > 0)
					transactions[i][0] = "+" + transactions[i][0];

				$('#transactionTableBody').append(
					$("<tr>")
				.append(
					$("<td>")
				.append(
					dateTransaction
				))
				.append(
					$("<td>")
				.append(
					'<a href="' + link + '">' + transactions[i][1] + '</a>'
				))
				.append(
					$("<td>")
				.append(
					transactions[i][0] + "&euro;"
				).addClass(amountClass)));
			}
		}
	).fail(//show error message from api
		function( errorMessage ) {
			alert(errorMessage.responseText);
		}
	);
}
