# Installation instructions:

1. Copy script to (you must do this on every workstation!):

   $METPATH/python/Custom/HR_CROCONTROL/Plugins/Kernel/
   (replace HR_CROCONTORL with your organisation name)
   IMPORTANT THING IS TO HAVE __init__.py file in every subdirectory!!!

3. Execute in shell:

   iplugins --update

   kutil f | grep ccl

4. Test custom function (shell):

   equationd 'v350[2,1] v-65[2,0] Fccl_cth_theta_e_python$v21v20$v37'
