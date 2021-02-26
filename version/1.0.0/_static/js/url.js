/*
$( document ).ready(function() {
    $(".highlight pre").each(function() {
	var text = $(this).text();
	$("h1").text(window.location)
	var targzurl = window.location.href
	var myurl = targzurl.substring(0, targzurl.lastIndexOf('/'));
	myurl = myurl.substring(0, myurl.lastIndexOf('/'));
	myurl = myurl.substring(0, myurl.lastIndexOf('/'));
	myurl = myurl.substring(0, myurl.lastIndexOf('/'));
	myurl = myurl + '/sasoptpy.tar.gz';
	text = text.replace("*url-to-sasoptpy.tar.gz*", myurl);
	$(this).text(text);
    });
});
*/
