$('#start').show();

function newAccount() {
	$('.view').hide();
	$('#newAccount').show();
}

credentials = {
	name: null,
	password: null,
}

function login() {
	credentials.name = $('#InputUsername').val();
	credentials.password = $('#InputPassword').val();

	$.post( //pass login credentials to api
		"/api/account/view", credentials,
	).done( //on successful login call dashboard()
		function( accountData ) {
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
	getPaymentData();
}

function getPaymentData() {
	$.post( //fetch transaction log from api
		"/api/money/view", credentials,
	).done(//fetched transactionData successfully
		function( transactionData ) {
			transactions = jQuery.parseJSON(transactionData);
			for(i = 0; i < transactions.length; i++) {
				//format unix time stamp to human readable format
				dateTransaction = new Date(transactions[i][2]*1000).toLocaleDateString();
				dateTransaction += " " + new Date(transactions[i][2]*1000).toLocaleTimeString();

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
					transactions[i][1]
				))
				.append(
					$("<td>")
				.append(
					transactions[i][0]
				)));
			}
		}
	).fail(//show error message from api
		function( errorMessage ) {
			alert(errorMessage.responseText);
		}
	);
}
