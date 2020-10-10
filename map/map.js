const googleMap = new Vue({
    el:'#app',
    data:{
        map:null,
        features:[],
        infowindowAll:{}
    },
    methods:{
        initMap(){
            let location = {
                lat:25.021710,
                lng:121.542691
            };
            this.map = new google.maps.Map(document.getElementById('map'),{
                center: location,
                zoom:20,
                mapTypeId:'terrain'
            });

            fetch('./map.geojson')
                .then(results=>results.json())
                .then(result=>{
                    let res = result.features;

                    Array.prototype.forEach.call(res,r=>{
                        let latlng = new google.maps.LatLng(r.geometry.coordinates[0],r.geometry.coordinates[1]);
                        let marker = new google.maps.Marker({
                            position:latlng,
                            icon:{url:"https://www.flaticon.com/svg/static/icons/svg/3603/3603479.svg",scaledSize:new google.maps.Size(40,40)},
                            map:this.map

                        });
                        let full = 100;
                        let avaliable = 10;
                        
                        var css = document.getElementById('css');
                        var pie = document.getElementsByClassName('pie');
                        var c = css.sheet;
                        var str = ".pie.pie::before{animation-delay:-"+(full-avaliable)+"s;}";
                        
                        let infowindow = new google.maps.InfoWindow({
                            content: `<h4>${r.properties.name}</h4>`
                            +`<h6>剩餘空位：${avaliable}/${full}</h6>`
                            +`<div class="pie"></div>`
                        });
                        c.insertRule(str,0);

                        marker.addListener('click',e=>{
                            infowindow.open(this.map,marker);
                        });

                        this.infowindowAll[r.properties.id]={
                            open: function(){
                                infowindow.open(this.map,marker);
                            }
                        };
                    });
                });

        },
        openInfoWindows(id){
            this.infowindowAll[id].open();
        }
    },
    created(){
        window.addEventListener('load',()=>{
            this.initMap();
        });
    }
});