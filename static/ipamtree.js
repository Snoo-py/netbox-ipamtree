

function STATUS_TEMPLATE(netbox) {
  if (!netbox) {
    return '—'
  }
  if (netbox.free_ips) {
    return `<span class="badge bg-success">Available</span>`;
  }
  return `<span class="badge text-bg-${netbox.status_color}">${netbox.status}</span>`;
};

function ROLE_TEMPLATE(netbox) {
  if (!netbox) {
    return '—'
  };
  if (netbox.prefix || netbox.free_ips) {
    return '—'
  };
  return `<span class="badge text-bg-${netbox.role_color}">${netbox.role}</span>`;
};

function UTILIZATION_TEMPLATE(netbox) {
  if (!netbox) {
    return '—'
  }
  if (!netbox.prefix) {
    return '—'
  };
  if (netbox.status == "Available") {
    return '—'
  };
  var utilization = netbox.utilization;
  data = '<div class="progress text-center">\r\n'
  var width = utilization;
  if (utilization > 100) {
    width = 100;
  };
  var progress = 'success';
  if (utilization >= 90) {
    progress = 'danger';
  } else if (utilization >= 75) {
    progress = 'warning';
  };
  data += `<div class="progress-bar bg-${progress}" role="progressbar" aria-valuenow="${utilization}" aria-valuemin="0" aria-valuemax="100" style="width: ${width}%">`
  if (utilization >= 30 ) {
    data += `${utilization}%`
    data += '</div>'
  } else {
    data += '</div>'
    data += `<span class="progress-label"">${utilization}%</span>\r\n`
  };
  data += '</div>';
  return data;
};

function DESCRIPTION_TEMPLATE(netbox) {
  if (!netbox) {
    return '—'
  }
  var text = netbox.description;
  if (netbox.device && netbox.device != 'None') {
    text += ` (<a href="${netbox.device_url}">${netbox.device}</a>)`
  }
  if (!text || text == 'None') {
    return '—';
  };
  return text;
};

function std_text(text) {
  if (!text || text == 'None') {
    return '—';
  };
  return text;
}

$(function(){ $("#tree").fancytree({
        extensions: ["table", "glyph"],
        icon: true,
        table: {
          indentation: 16,      // indent 20px per node level
          nodeColumnIdx: 0,     // render the node title into the 2nd column
        },
        glyph: {
          preset: "",
          map: {
            _addClass: 'mdi',
            error: 'mdi-exclamation-triangle',
            expanderClosed: 'mdi-chevron-right',
            expanderLazy: 'mdi-chevron-right',
            expanderOpen: 'mdi-chevron-down',
            loading: 'mdi-empty',
            noExpander: 'mdi-empty',
            doc: 'mdi-info-circle',
            docOpen: 'mdi-info-circle',
            folder: 'mdi-cloud',
            folderOpen: 'mdi-cloud'
          }
        },
        source: {url: '/api/plugins/ipam-tree/fancytree/'},

        lazyLoad: function(event, data){
          var node = data.node;
          data.result = {
            url: '/api/plugins/ipam-tree/fancytree/' + node.key,
            data: {mode: "children", parent: node.key},
            cache: false
          };
       },
       renderColumns: function(event, data) {
        var node = data.node,
        $tdList = $(node.tr).find(">td");
        $(node.tr).eq(0)
        if (node.data.netbox && node.data.netbox.free_ips) {
          $(node.tr).eq(0).attr("style", "background-color: #a3cfbb");
        };
        if (node.data.netbox && node.data.netbox.status == "Available") {
          $(node.tr).eq(0).attr("style", "background-color: #a3cfbb");
        };
        $tdList.eq(1).html(DESCRIPTION_TEMPLATE(node.data.netbox));
        $tdList.eq(2).html(STATUS_TEMPLATE(node.data.netbox));
        $tdList.eq(3).html(ROLE_TEMPLATE(node.data.netbox));
        $tdList.eq(4).html(UTILIZATION_TEMPLATE(node.data.netbox));
        if (node.data.netbox) {
          $tdList.eq(5).text(std_text(node.data.netbox.site));
          $tdList.eq(6).text(std_text(node.data.netbox.vlan));
        };
      },
  });
});

