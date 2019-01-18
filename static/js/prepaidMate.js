$('#start').show();

function newAccount() {
	$('.view').hide();
	$('#newAccount').show();
}

function login() {
	$('.view').hide();
	$('#dashboard').show();

	credentials = {
		name:$('#InputUsername').val(),
		password:$('#InputPassword').val(),
	}

	$.post(
		"/api/account/view", credentials,
	).done(
		function( data ) {
			alert("login successful! "+ $.parseJSON(data)[4]);
		}
	).fail(
		function (data ) {
			alert("error: "+ data.responseText);
		}
	);
}
