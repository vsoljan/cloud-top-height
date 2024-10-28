*Installation instructions:*

1. Copy script to (every workstation!):
   
$METPATH/python/IBL/Plugins/Kernel/

3. Execute in shell:

iplugins --update

kutil f | grep ccl

4. Test custom function (shell):

equationd 'v350[2,1] v-65[2,0] Fccl_cth_theta_e_python$v21v20$v37'
