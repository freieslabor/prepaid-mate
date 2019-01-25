$('#start').show();

function newAccount() {
	$('.view').hide();
	$('#newAccount').show();
}

function login() {
	credentials = {
		name:$('#InputUsername').val(),
		password:$('#InputPassword').val(),
	}

	$.post(
		"/api/account/view", credentials,
	).done(
		function( data ) {
			dashboard();
		}
	).fail(
		function (data ) {
			alert("Falscher Nutzername oder Passwort!");
		}
	);
}

function dashboard() {
	$('.view').hide();
	$('#dashboard').show();
}
