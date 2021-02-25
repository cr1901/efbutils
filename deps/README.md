Dependencies for experiments, like `ufmecho`, go in this directory and are
not part of `efbutils` proper.

Some Dependencies are provided by Lattice Reference Design \#1126. `rd1126`
can be downloaded [here](https://www.latticesemi.com/products/designsoftwareandip/intellectualproperty/referencedesigns/referencedesign04/ram-typeinterfaceforembedded-ufm).
Copy out the following files relative to the `rd1126` directory and place them
here:

* `source/verilog/ufm_wb_top.v`
* `source/verilog/efb_define_def.v`
* `source/verilog/ipexpress/EFB_UFM.v`
* `source/verilog/ipexpress/USR_MEM.v`

Additionally, apply the following patch to `EFB_UFM.v`:

```diff
--- EFB_UFM0.v  2021-02-25 17:48:25.685557100 -0500
+++ EFB_UFM.v   2021-02-25 17:48:39.385308100 -0500
@@ -26,8 +26,8 @@
     VLO scuba_vlo_inst (.Z(scuba_vlo));

     defparam EFBInst_0.UFM_INIT_FILE_FORMAT = "HEX" ;
-    defparam EFBInst_0.UFM_INIT_FILE_NAME = "NONE" ;
-    defparam EFBInst_0.UFM_INIT_ALL_ZEROS = "ENABLED" ;
+    defparam EFBInst_0.UFM_INIT_FILE_NAME = "init.mem" ;
+    defparam EFBInst_0.UFM_INIT_ALL_ZEROS = "DISABLED" ;
     defparam EFBInst_0.UFM_INIT_START_PAGE = 0 ;
     defparam EFBInst_0.UFM_INIT_PAGES = 511 ;
     defparam EFBInst_0.DEV_DENSITY = "1200L" ;
```
