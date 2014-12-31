<%!from desktop.views import commonheader, commonfooter %>
<%namespace name="shared" file="shared_components.mako" />

${commonheader("Caspar App", "caspar_app", user) | n,unicode}
${shared.menubar(section)}
<%! import os %>
## Use double hashes for a mako template comment
## Main body
<style type="text/css">
#tablerows td div{ cursor: pointer; cursor: hand; border:1px solid #eee; margin:2px 5px; float:left;}
</style>
<script type="text/javascript">
function editcell(cluster, table, rowkey, column, timestamp, lastvalue){
  $.post('/caspar_app/hbaseapi/?action=editcell', {cluster:cluster, table:table, rowkey:rowkey, column:column, timestamp:timestamp}, function(result){
    console.log(result)
    if(result){
      var cellhistory = $('#updaterowtable');
      cellhistory.empty();
      cellhistory.append('<tr><td>Row Key:</td><td colspan="2"><input type="hidden" name="cluster" value="' + cluster + '" /><input type="hidden" name="table" value="' + table + '" /><input type="text" name="rowkey" value="' + rowkey + '" readonly /></td><td align="right"><input type="button" value="submit" onclick="submitupdaterow()"/><input type="button" value="close" onclick="$(\'#updaterowtable\').hide()" /></td></tr>');
      cellhistory.append('<tr><td>family:column_name </td><td><input type="text" name="columnname" value="' + column +'" readonly /></td><td>value </td><td><input type="text" name="columnvalue" value="' + lastvalue + '" /></td></tr>');
      if(result.data.length){
        cellhistory.append('<tr><th colspan="2" align="left">History:</th></tr>');
      }
      for(var x = 0; x < result.data.length; x++){
        cellhistory.append('<tr><td>family:column_name </td><td><input type="text" value="' + column +'" readonly /><td>value </td><td><input type="text" value="' + result.data[x].value + '" readonly /> timestamp:' + new Date(result.data[x].timestamp) + '</td></tr>');
      }
      cellhistory.show();
    }else{
    }
  })
}
function submitupdaterow(){
  $.post('/caspar_app/hbaseapi/?action=updaterow', $('#updaterowtable :input').serialize(), function(result){
    if(result.status){
      $('#updaterowtable').hide();
      $('#updaterowtable :text').val('');
      $.jHueNotify.info(result.msg);
      fetchTableRows($('#updaterowtable :input[name="cluster"]').val(), $('#updaterowtable :input[name="table"]').val())
    }else{
      $.jHueNotify.error(result.msg);
    }
  })
}
function searchrow(cluster, table){
  $.post('/caspar_app/hbaseapi/?action=disabletable', {cluster:cluster, table:table}, function(result){
    if(result.status){
      $.jHueNotify.info(result.msg);
      window.location.reload();
    }else{
      $.jHueNotify.error(result.msg);
    }
  })
}
function enatable(cluster, table){
  $.post('/caspar_app/hbaseapi/?action=enabletable', {cluster:cluster, table:table}, function(result){
    if(result.status){
      $.jHueNotify.info(result.msg);
      window.location.reload();
    }else{
      $.jHueNotify.error(result.msg);
    }
  })
}
function distable(cluster, table){
  $.post('/caspar_app/hbaseapi/?action=disabletable', {cluster:cluster, table:table}, function(result){
    if(result.status){
      $.jHueNotify.info(result.msg);
      window.location.reload();
    }else{
      $.jHueNotify.error(result.msg);
    }
  })
}
function deltable(cluster, table){
  $.post('/caspar_app/hbaseapi/?action=deletetable', {cluster:cluster, table:table}, function(result){
    if(result.status){
      $.jHueNotify.info(result.msg);
      window.location.reload();
    }else{
      $.jHueNotify.error(result.msg);
    }
  })
}
function shownewtable(cluster){
  $('#newtable').show();
  $('#newtable :hidden[name=cluster]').val(cluster);
}
function submitnewtable(){
  $.post('/caspar_app/hbaseapi/?action=createtable', $('#newtable :input').serialize(), function(result){
    if(result.status){
      $('#newtable').hide();
      $('#newtable :text').val('');
      $.jHueNotify.info(result.msg);
      window.location.reload();
    }else{
      $.jHueNotify.error(result.msg);
    }
  })
}
function delrow(cluster, table, rowkey){
  $.post('/caspar_app/hbaseapi/?action=deleterow', {cluster:cluster, table:table, rowkey:rowkey}, function(result){
    if(result.status){
      $.jHueNotify.info(result.msg);
      fetchTableRows(cluster, table);
    }else{
      $.jHueNotify.error(result.msg);
    }
  })
}
function shownewrow(cluster, table){
  $('#newrowtable').show();
  $('#newrowtable :hidden[name=cluster]').val(cluster);
  $('#newrowtable :hidden[name=table]').val(table);
}
function submitnewrow(){
  $.post('/caspar_app/hbaseapi/?action=addnewrow', $('#newrowtable :input').serialize(), function(result){
    if(result.status){
      $('#newrowtable').hide();
      $('#newrowtable :text').val('');
      $.jHueNotify.info(result.msg);
      fetchTableRows($('#newrowtable :input[name="cluster"]').val(), $('#newrowtable :input[name="table"]').val())
    }else{
      $.jHueNotify.error(result.msg);
    }
  })
}
function fetchTableColumnDescription(cluster, table){

}
function showsearchbar(cluster, table){
  var tableObj = $('#tablerows');
  tableObj.prev('#searchline').remove();
  tableObj.before('<div id="searchline">Search:<input type="text" name="searchval" id="searchval" /> <input type="button" value="search" onclick="fetchTableRows(\'' + cluster + '\', \'' + table + '\', {rowkey:$(\'#searchval\').val()}, function(){})" style="margin-bottom:10px;" /></div>');
}
function fetchTableRows(cluster,table,params,endcallback) {
  console.log(cluster,table);
  $.getJSON('/caspar_app/hbaseapi/',{action:'getColumnDescriptors', cluster:cluster, table:table}, function(result){
      console.log(result);
    }
  )
  $.getJSON('/caspar_app/hbaseapi/',{action:'getrows', cluster:cluster, table:table, params:params}, function(result){
    if (result.data) {
      console.log(result);
      var tableObj = $('#tablerows');
      tableObj.empty();
      tableObj.prevAll('p').first().empty().append('Table Rows: <span><a href="#" onclick="shownewrow(\'' + cluster + '\', \'' + table + '\')">New Row</a></span>');
      for(var x = 0; x < result.data.length; x++){
        var rowkey = $('<td width="5%"><input type="button" name="delrowkey[]" value="Del Row" onclick="delrow(\'' + cluster + '\', \'' + table + '\', \'' + result.data[x].row + '\')" /></td><td width="10%">' + result.data[x].row + '</td>');
        var rowval = $('<td width="85%"></td>');
        for(var c in result.data[x].columns){
          rowval.append('<div onclick="editcell(\'' + cluster + '\', \'' + table + '\', \'' + result.data[x].row + '\', \'' + c + '\', ' + result.data[x].columns[c].timestamp + ', $(this).find(\'span\').last().text())"><span>' + c + '</span><br/><span>' + result.data[x].columns[c].value + '</span></div>');
        }
        tableObj.append($('<tr></tr>').append(rowkey).append(rowval));
      }
      // endcallback();
    }
  })

}
</script>
<div class="container-fluid">
  <div class="card">
    <h2 class="card-heading simple"></h2>
    <div class="card-body">
      <p>Cluster:</p>
      <select name="selectedcluster" id="selectedcluster">
        % for c in clusterlist:
        <option value="${c['name']}">${c['name']}</option>
        % endfor
      </select>
      <p></p>
      <p>Tables: <span><a href="#" onclick="shownewtable($('#selectedcluster').val())">New Table</a></span></p>
      <table id="newtable" cellspacing="5" cellpadding="5" style="display:none;">
        <tr>
          <td>Table Name:</td>
          <td><input type="hidden" name="cluster" /><input type="text" name="tablename" /></td>
          <td><input type="button" value="submit" onclick="submitnewtable()" /> <input type="button" value="close" onclick="$('#newtable').hide()" /></td>
        </tr>
        <tr>
          <td>Column Family:</td>
          <td colspan="2"><input type="text" name="cf" /></td>
        </tr>
      </table>
      <table width="100%" border="1">
      <tr>
        <th width='3%' align='right'>&nbsp;</th>
        <th width='' align='left'>Table Name</th>
        <th width='3%' align="left">Action</th>
      </tr>
      % for t in tablelist:
      <tr>
        <td align='center'>
          <input type="button" name="deltable" value="Del Table" onclick="deltable($('#selectedcluster').val(), '${t['name']}')" />
        </td>
        <td>
          <a href='#' onclick="fetchTableRows($('#selectedcluster').val(), '${t['name']}', {}, showsearchbar($('#selectedcluster').val(), '${t['name']}'))">${t['name']}</a>
        </td>
        <td>
          % if t['enabled']:
          <input type="button" name="distable" value="Disable Table" onclick="distable($('#selectedcluster').val(), '${t['name']}')" />
          % else:
          <input type="button" name="enatable" value="Enable Table" onclick="enatable($('#selectedcluster').val(), '${t['name']}')" />
          % endif
        </td>
      </tr>
      % endfor
      </table>
      <p></p>
      <p></p>
      <table id="newrowtable" cellspacing="5" cellpadding="5" style="display:none;">
        <tr>
          <td>Row Key:</td>
          <td colspan="2"><input type="hidden" name="cluster" /><input type="hidden" name="table" />
          <input type="text" name="rowkey" value="" /></td>
          <td align="right"><input type="button" value="submit" onclick="submitnewrow()"/> <input type="button" value="close" onclick="$('#newrowtable').hide()" /></td>
        </tr>
        <tr>
          <td>family:column_name </td>
          <td><input type="text" name="columnname" value="" /></td>
          <td>value </td>
          <td><input type="text" name="columnvalue" value="" /></td>
        </tr>
      </table>
      <table id="updaterowtable" cellspacing="5" cellpadding="5" style="display:none;">
      </table>
      <table widht="100%" border="1" id="tablerows">
      </table>
      ## <table id="updaterowtable" cellspacing="5" cellpadding="5" style="display:none;">
      ## </table>
    </div>
    <div class="debug">
        ${debug}
        ${debug2}
    </div>
  </div>
</div>
${commonfooter(messages) | n,unicode}
