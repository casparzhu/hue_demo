<%!from desktop.views import commonheader, commonfooter %>
<%namespace name="shared" file="shared_components.mako" />

${commonheader("Caspar App", "caspar_app", user) | n,unicode}
${shared.menubar(section)}
<%! import os %>
## Use double hashes for a mako template comment
## Main body

<div class="container-fluid">
  <div class="card">
    <h2 class="card-heading simple">${currentdir}</h2>
    <div class="card-body">
      <form method="post" enctype="multipart/form-data" onchange="this.submit();">
        <p><input type="hidden" name="dest" value="${currentdir}" /><input type="file" name="hdfs_file" value="" /></p>
      </form>
      <table width="100%">
      <tr>
        <th width='30%' align='left'>Name</th>
        <th width='10%' align='left'>Size</th>
        <th width='10%' align='left'>Owner</th>
        <th width='10%' align='left'>Group</th>
        <th width='20%' align='left'>Permission</th>
        <th width='20%' align='left'>Date</th>
      </tr>
      % for f in dirinfo:
      <tr>
        <td>
            % if f['type'] in ('D','DIRECTORY'):
            <%  
                if f['name'] in ('..', '.'):
                    path = os.path.dirname(currentdir)
                elif currentdir == os.sep:
                    path = currentdir + f['name']
                else:
                    path = currentdir + os.sep + f['name']
            %>
            <a href='?type=${section}&dir=${path}'>${f['name']}</a>
            % else:
            ${f['name']}
            % endif
        </td>
        <td>${f['size']}</td>
        <td>${f['owner']}</td>
        <td>${f['group']}</td>
        <td>${f['mode']}</td>
        <td>${f['time']}</td>
      </tr>
      % endfor
      </table>
    </div>
    <div class="debug">
        ${debug}
        ${debug2}
    </div>
  </div>
</div>
${commonfooter(messages) | n,unicode}
