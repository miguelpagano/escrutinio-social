/* 
   Si pudimos determinar la mesa unívocamente, actualizamos la
   sección y el circuito (si están vacíos). 
*/
function cambioMesa(url_seccion,url_circuito){
    var mesa = $('#id_mesa').val();
    var circuito = $('#id_circuito').val();
    var seccion = $('#id_seccion').val();
    if(mesa != -1){
	var params = {'mesa': mesa, 'desdeMesa': '1'};
	if(circuito == -1){
	    updateFieldUrl('circuito',url_circuito, params);
	}
	if(seccion == -1){
	    updateFieldUrl('seccion',url_seccion,params);
	}
    }
    return true;
}

var updateDistrito = function(url){
    return(
	function(e){
	    updateField('distrito', url,[]);
	    return true;
	}
    )
}

var updateSeccion = function(url){
    return (
	function(e){
	    updateField(
		'seccion',
		url,
		['distrito']
	    );
	    return true;
	}
    )
}

var updateCircuito = function(url){
    return (
	function(e){
	    updateField(
		'circuito',
		url,
		['distrito','seccion']
	    );
	    return true;
	}
    )
}

var updateMesa = function(url,url_seccion,url_circuito){
    return (
	function(e){
	    updateField(
		'mesa',
		url,
		['distrito','seccion','circuito'],
		cambioMesa(url_seccion,url_circuito)
	    );
	    return true;
	}
    )
}