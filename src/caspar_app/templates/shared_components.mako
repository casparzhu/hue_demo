
<%!
def is_selected(section, matcher):
  if section == matcher:
    return "active"
  else:
    return ""
%>

<%def name="menubar(section='')">
  <div class="navbar navbar-inverse navbar-fixed-top nokids">
    <div class="navbar-inner">
      <div class="container-fluid">
        <div class="nav-collapse">
          <ul class="nav">
            <li class="currentApp">
              <a href="/caspar_app">
                <img src="/caspar_app/static/art/icon_caspar_app_48.png" class="app-icon" />
                Caspar App
              </a>
             </li>
             <li class="${is_selected(section, 'local')}"><a href="/caspar_app/?type=local">File System</a></li>
             <li class="${is_selected(section, 'hdfs')}"><a href="/caspar_app/?type=hdfs">HDFS</a></li>
             <li class="${is_selected(section, 'hbasedemo')}"><a href="/caspar_app/hbasedemo">HBase</a></li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</%def>
