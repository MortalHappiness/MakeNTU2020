const googleMap = new Vue({
  el: "#app",
  data: {
    map: null,
    features: [],
    infowindowAll: {},
  },
  methods: {
    initMap() {
      let location = {
        lat: 25.022071,
        lng: 121.543038
      };
      this.map = new google.maps.Map(document.getElementById("map"), {
        center: location,
        zoom: 18,
        mapTypeId: "terrain",
        zoomControl: false,
        mapTypeControl: false,
        scaleControl: false,
        streetViewControl: false,
        rotateControl: false,
        fullscreenControl: false
      });

      fetch("/api/stores")
        .then((results)=>results.json())
        .then((data)=>{
            const ret = {"type": "FeatureCollection","features":[]};
            data.forEach(item=>{
                ret.features.push({"type":"Feature","properties":{"id":item.latitude,"name":item.name,"max":item.max_capacity,"num":item.current_people,"queuing":item.queuing_num},"geometry":{"type":"Point","coordinates":[item.latitude,item.longitude]}}
        )})
            return ret;})
        .then((result) => {
          let res = result.features;

          Array.prototype.forEach.call(res, (r) => {
            let latlng = new google.maps.LatLng(
              r.geometry.coordinates[0],
              r.geometry.coordinates[1]
            );
            let marker = new google.maps.Marker({
              position: latlng,
              icon: {
                url:
                  "https://www.flaticon.com/svg/static/icons/svg/3603/3603479.svg",
                scaledSize: new google.maps.Size(40, 40),
              },
              map: this.map,
            });
            let full = r.properties.max;
            let num = r.properties.num;
            let queuing = r.properties.queuing;

            var css = document.getElementById("css");
            var pie = document.getElementsByClassName("pie");
            var c = css.sheet;
            var str =
              ".pie.pie::before{animation-delay:-" + (num/full) + "s;}";
            let infowindow = null;

            if (full!==num){
                infowindow = new google.maps.InfoWindow({
                content:
                  `<h4>${r.properties.name}</h4>` +
                  `<h6>剩餘空位：${full-num}/${full}</h6>` +
                  `<div class="pie"></div>`,
              });
             c.insertRule(str, 0);
          } else{
              infowindow = new google.maps.InfoWindow({
              content:
                `<h4>${r.properties.name}</h4>` +
                `<h6>座位已滿，${queuing}人排隊中</h6>` +
                `<div class="pie"></div>`,
            });
           c.insertRule(".pie.pie::before{animation-delay:-99.99s;}", 0);
          }


            marker.addListener("click", (e) => {
              infowindow.open(this.map, marker);
            });

            this.infowindowAll[r.properties.id] = {
              open: function () {
                infowindow.open(this.map, marker);
              },
            };
          });
        });
    },
    openInfoWindows(id) {
      this.infowindowAll[id].open();
    },
  },
  created() {
    window.addEventListener("load", () => {
      this.initMap();
    });
  },
});
