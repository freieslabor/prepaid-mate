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
				dateTransaction = new Date(transactions[i][2]*1000).toLocaleDateString();
				dateTransaction += " " + new Date(transactions[i][2]*1000).toLocaleTimeString();
				$('#transactionTableBody').append(
						"<tr> \
						<td>"+dateTransaction+"</td> \
						<td>"+transactions[i][1]+"</td> \
						<td>"+transactions[i][0]/100 +"&euro;</td> \
						</tr>"
					);
			}

		}
	).fail(//show error message from api
		function( errorMessage ) {
			alert(errorMessage.responseText);
		}
	);
}
