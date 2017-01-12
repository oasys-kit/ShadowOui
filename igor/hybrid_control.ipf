Function hybrid_control()
	sh_kill_plots("sh_gui")
	Execute "sh_gui()"
	sh_kill_plots("hybrid_gui")
	Execute "hybrid_gui()"	
End

Function sh_control()
	sh_kill_plots("sh_gui")
	SetDataFolder root:
	Execute "sh_gui()"	
End

Window hybrid_gui() : Graph
	PauseUpdate; Silent 1
	Display/k=1 /W=(480,50,820,450)
	Modifygraph gbRGB=(42662,65535,42662)
	String/G ghy_path
	If(exists("gsh_path")==2)
		ghy_path = gsh_path
	else
		ghy_path = "C:xop2.3:tmp:"
	endif
	Variable/G ghy_n_oe = 1
	Variable/G ghy_n_screen = 2
	Variable/G ghy_diff_plane = 2
	Variable/G ghy_calcType = 1
	Variable/G ghy_focallength = -1
	Variable/G ghy_distance = -1
	String/G ghy_mirrorfile = "mirror.dat"
	Variable/G ghy_usemirrorfile = 1
	Variable/G ghy_nbins_x = 200
	Variable/G ghy_nbins_z = 200
	Variable/G ghy_npeak = 20
	Variable/G ghy_lengthunit = 1
	Variable/G ghy_fftnpts = 1e6
	Variable/G ghy_scalefactor = 1
	Variable/G ghy_nf = 0
	Variable/G ghy_nf_only = 0
	Variable/G ghy_range_x = -1
	Variable/G ghy_range_z = -1
	Variable/G ghy_nncon_x = 401
	Variable/G ghy_nncon_z = 401
	SetVariable hy_input_path,live=1,pos={0,10},size={0,0},bodyWidth=160,fsize=14,title="Hybrid working directory",value=ghy_path
	SetVariable hy_input_n_oe,live=1,pos={0,35},size={0,0},bodyWidth=50,fsize=14,title="O.E. number",limits={0,10,1},value=ghy_n_oe
	SetVariable hy_input_n_screen,live=1,pos={0,60},size={0,0},bodyWidth=50,fsize=14,title="Screen number at 0 distance after OE",limits={0,10,1},value=ghy_n_screen
	PopupMenu/Z hy_input_diff_plane,live=1,pos={0,85},size={0,0},bodyWidth=80,fsize=14,title="Diffraction plane",mode=1,popvalue=StringFromList(ghy_diff_plane-1, "X;Z;2D"),value="X;Z;2D",proc=hy_updategui_diff_plane
	PopupMenu/Z hy_input_calcType,live=1,pos={0,115},size={0,0},bodyWidth=220,fsize=14,title="Calculation type",mode=1,popvalue=StringFromList(ghy_calcType-1, "1.Simple aperture;2.Ideal focusing optics;3.Mirror with slope error;4.Grating with slope error;5.CRL"),value="1.Simple aperture;2.Ideal focusing optics;3.Mirror with slope error;4.Grating with slope error;5.CRL",proc=hy_updategui_calcType
	SetVariable hy_input_focallength, disable=2,live=1,pos={0,145},size={0,0},bodyWidth=80,fsize=14,title="Focal length (use SIMAGE if <0)",value=ghy_focallength
	SetVariable hy_input_distance, disable=0,live=1,pos={0,170},size={0,0},bodyWidth=80,fsize=14,title="Distance to image (use T_IMAGE if <0)",value=ghy_distance
	SetVariable hy_input_mirrorfile,disable=2,live=1,pos={0,195},size={0,0},bodyWidth=160,fsize=14,title="Mirror figure error file",value=ghy_mirrorfile
	PopupMenu/Z hy_input_mirrorwave,disable=2,live=1,pos={0,220},size={0,0},bodyWidth=120,fsize=14,title="        Or, select wave",mode=1,popvalue=StringFromList(ghy_usemirrorfile-1,sh_popwave()),value=sh_popwave()
	PopupMenu/Z hy_input_nearfield,disable=2,live=1,pos={0,245},size={0,0},bodyWidth=80,fsize=14,title="Near-field calculation",mode=1,popvalue=StringFromList(ghy_nf,"No;YES"),value="No;YES",proc=hy_updategui_ghy_nf
	GroupBox hy_input_gb1,pos={0,275},size={330,1},frame=0
	TitleBox hy_input_tb1,title="Numerical control parameters",pos={50,282},frame=0,fsize=14,fColor=(65535,0,0),fstyle=2
	SetVariable hy_input_nbins_x, disable=2,live=1,pos={0,305},size={0,0},bodyWidth=80,fsize=14,title="Number of bins for I(X) histogram",value=ghy_nbins_x
	SetVariable hy_input_nbins_z, disable=0,live=1,pos={0,330},size={0,0},bodyWidth=80,fsize=14,title="Number of bins for I(Z) histogram",value=ghy_nbins_z
	SetVariable hy_input_npeak, disable=0,live=1,pos={0,355},size={0,0},bodyWidth=80,fsize=14,title="Number of diffraction peaks",value=ghy_npeak
	SetVariable hy_input_fftnpts, disable=0,live=1,pos={0,380},size={0,0},bodyWidth=80,fsize=14,title="Maximum number of points for FFT",value=ghy_fftnpts
	SetVariable hy_input_scalefactor, disable=0,live=1,pos={0,405},size={0,0},bodyWidth=80,fsize=14,title="Scale factor for wavefront size",value=ghy_scalefactor
	GroupBox hy_input_gb2,pos={0,435},size={330,1},frame=0
	PopupMenu/Z hy_input_lengthunit,live=1,pos={0,440},size={0,0},bodyWidth=80,fsize=14,fColor=(65535,0,0),title="Important! Length unit in SHADOW",mode=1,popvalue=StringFromList(ghy_lengthunit-1, "cm;mm"),value="cm;mm",proc=hy_updategui_lengthunit
	GroupBox hy_input_gb3,pos={0,470},size={330,1},frame=0
	TitleBox hy_input_tb2,title="Result plotting control",pos={50,477},frame=0,fsize=14,fColor=(65535,0,0),fstyle=2
	SetVariable hy_input_range_x, disable=2,live=1,pos={0,500},size={0,0},bodyWidth=80,fsize=14,title="Result histogram range (X) user unit",value=ghy_range_x
	SetVariable hy_input_nncon_x, disable=2,live=1,pos={0,525},size={0,0},bodyWidth=80,fsize=14,title="Result histogram number of bins (X)",value=ghy_nncon_x
	SetVariable hy_input_range_z, disable=0,live=1,pos={0,550},size={0,0},bodyWidth=80,fsize=14,title="Result histogram range (Z) user unit",value=ghy_range_z
	SetVariable hy_input_nncon_z, disable=0,live=1,pos={0,580},size={0,0},bodyWidth=80,fsize=14,title="Result histogram number of bins (Z)",value=ghy_nncon_z	
	GroupBox hy_input_gb4,pos={0,605},size={510,1},frame=0
	GroupBox hy_input_gb5,pos={332,0},size={1,605},frame=0		
	Button hy_input_run,pos={340,10},size={160,30},fsize=16,fColor=(65535,0,0),proc=hy_run,title="Run HYBRID"
	Button hy_input_rerun,win=hybrid_gui,disable=2,pos={340,45},size={160,30},fsize=16,proc=hy_rerun,title="Rerun (no file load)"
	Button hy_input_savefiles,pos={340,80},size={160,30},fsize=14,proc=hy_savefiles,title="Save shadow files"
	Button hy_input_showplots,pos={340,115},size={160,30},fsize=14,proc=hy_showplots,title="Show plots"
	Button hy_input_closeplots,pos={340,150},size={160,30},fsize=14,proc=hy_closeplots,title="Close plots"
	GroupBox hy_input_gb6,pos={335,185},size={170,1},frame=0
	TitleBox hy_input_tb3,title="Post run studies",pos={350,190},frame=0,fsize=14,fColor=(65535,0,0),fstyle=2
	Button hy_input_sestudy,disable=2,pos={340,210},size={160,30},fsize=14,proc=hy_sestudy,title="Slope error study"
	Button hy_input_longi,disable=2,pos={340,245},size={160,30},fsize=14,proc=hy_longi,title="longitudinal profiles (nf)"
	GroupBox hy_input_gb7,pos={335,500},size={170,1},frame=0	
	Button hy_input_cleanup,pos={340,510},size={160,30},fsize=14,fColor=(0,0,65535),proc=hy_cleanup,title="Clean everything"
	Button hy_input_restartgui,pos={340,545},size={160,30},fsize=14,fColor=(0,0,65535),proc=hy_restartgui,title="Reset GUI"
EndMacro

Function hy_restartgui(hy_input_restartgui) : ButtonControl
	String hy_input_restartgui
	sh_kill_plots("hybrid_gui")
	Execute "hybrid_gui()"		
End

Function/S sh_popwave()
	String listwave
	listwave = "use file;"+Wavelist("*",";","")
	return listwave
End

Function hy_updategui_lengthunit(ctrlName,popNum,popStr) : PopupMenuControl
	String ctrlName
	Variable popNum	// which item is currently selected (1-based)
	String popStr		// contents of current popup item as string 
	NVAR ghy_lengthunit
	ghy_lengthunit = popNum
end

Function hy_updategui_ghy_nf(ctrlName,popNum,popStr) : PopupMenuControl
	String ctrlName
	Variable popNum	// which item is currently selected (1-based)
	String popStr		// contents of current popup item as string 
	NVAR ghy_nf
	ghy_nf = popNum-1
end

Function hy_updategui_diff_plane(ctrlName,popNum,popStr) : PopupMenuControl
	String ctrlName
	Variable popNum	// which item is currently selected (1-based)
	String popStr		// contents of current popup item as string
	NVAR ghy_diff_plane
	ghy_diff_plane = popNum
	If(popNum==1)
		SetVariable hy_input_nbins_x, win=hybrid_gui, disable=0,live=1,pos={0,305},size={0,0},bodyWidth=80,fsize=14,title="Number of bins for I(X) histogram",value=ghy_nbins_x
		SetVariable hy_input_nbins_z, win=hybrid_gui, disable=2,live=1,pos={0,330},size={0,0},bodyWidth=80,fsize=14,title="Number of bins for I(Z) histogram",value=ghy_nbins_z
		SetVariable hy_input_range_x, disable=0,live=1,pos={0,475},size={0,0},bodyWidth=80,fsize=14,title="Result histogram range (X) user unit",value=ghy_range_x
		SetVariable hy_input_nncon_x, disable=0,live=1,pos={0,500},size={0,0},bodyWidth=80,fsize=14,title="Result histogram number of bins (X)",value=ghy_nncon_x
		SetVariable hy_input_range_z, disable=2,live=1,pos={0,525},size={0,0},bodyWidth=80,fsize=14,title="Result histogram range (Z) user unit",value=ghy_range_z
		SetVariable hy_input_nncon_z, disable=2,live=1,pos={0,550},size={0,0},bodyWidth=80,fsize=14,title="Result histogram number of bins (Z)",value=ghy_nncon_z	
	Else
		SetVariable hy_input_nbins_x, win=hybrid_gui, disable=2,live=1,pos={0,305},size={0,0},bodyWidth=80,fsize=14,title="Number of bins for I(X) histogram",value=ghy_nbins_x
		SetVariable hy_input_nbins_z, win=hybrid_gui, disable=0,live=1,pos={0,330},size={0,0},bodyWidth=80,fsize=14,title="Number of bins for I(Z) histogram",value=ghy_nbins_z
		SetVariable hy_input_range_x, disable=2,live=1,pos={0,475},size={0,0},bodyWidth=80,fsize=14,title="Result histogram range (X) user unit",value=ghy_range_x
		SetVariable hy_input_nncon_x, disable=2,live=1,pos={0,500},size={0,0},bodyWidth=80,fsize=14,title="Result histogram number of bins (X)",value=ghy_nncon_x
		SetVariable hy_input_range_z, disable=0,live=1,pos={0,525},size={0,0},bodyWidth=80,fsize=14,title="Result histogram range (Z) user unit",value=ghy_range_z
		SetVariable hy_input_nncon_z, disable=0,live=1,pos={0,550},size={0,0},bodyWidth=80,fsize=14,title="Result histogram number of bins (Z)",value=ghy_nncon_z	
	Endif
	If(popNum==2)
		SetVariable hy_input_nbins_x, win=hybrid_gui, disable=2,live=1,pos={0,305},size={0,0},bodyWidth=80,fsize=14,title="Number of bins for I(X) histogram",value=ghy_nbins_x
		SetVariable hy_input_nbins_z, win=hybrid_gui, disable=0,live=1,pos={0,330},size={0,0},bodyWidth=80,fsize=14,title="Number of bins for I(Z) histogram",value=ghy_nbins_z
		SetVariable hy_input_range_x, disable=2,live=1,pos={0,475},size={0,0},bodyWidth=80,fsize=14,title="Result histogram range (X) user unit",value=ghy_range_x
		SetVariable hy_input_nncon_x, disable=2,live=1,pos={0,500},size={0,0},bodyWidth=80,fsize=14,title="Result histogram number of bins (X)",value=ghy_nncon_x
		SetVariable hy_input_range_z, disable=0,live=1,pos={0,525},size={0,0},bodyWidth=80,fsize=14,title="Result histogram range (Z) user unit",value=ghy_range_z
		SetVariable hy_input_nncon_z, disable=0,live=1,pos={0,550},size={0,0},bodyWidth=80,fsize=14,title="Result histogram number of bins (Z)",value=ghy_nncon_z	
	Else
		SetVariable hy_input_nbins_x, win=hybrid_gui, disable=0,live=1,pos={0,305},size={0,0},bodyWidth=80,fsize=14,title="Number of bins for I(X) histogram",value=ghy_nbins_x
		SetVariable hy_input_nbins_z, win=hybrid_gui, disable=2,live=1,pos={0,330},size={0,0},bodyWidth=80,fsize=14,title="Number of bins for I(Z) histogram",value=ghy_nbins_z
		SetVariable hy_input_range_x, disable=0,live=1,pos={0,475},size={0,0},bodyWidth=80,fsize=14,title="Result histogram range (X) user unit",value=ghy_range_x
		SetVariable hy_input_nncon_x, disable=0,live=1,pos={0,500},size={0,0},bodyWidth=80,fsize=14,title="Result histogram number of bins (X)",value=ghy_nncon_x
		SetVariable hy_input_range_z, disable=2,live=1,pos={0,525},size={0,0},bodyWidth=80,fsize=14,title="Result histogram range (Z) user unit",value=ghy_range_z
		SetVariable hy_input_nncon_z, disable=2,live=1,pos={0,550},size={0,0},bodyWidth=80,fsize=14,title="Result histogram number of bins (Z)",value=ghy_nncon_z	
	Endif
	If((popNum==3)||(popNum==4))
		SetVariable hy_input_nbins_x, win=hybrid_gui, disable=0,live=1,pos={0,305},size={0,0},bodyWidth=80,fsize=14,title="Number of bins for I(X) histogram",value=ghy_nbins_x
		SetVariable hy_input_nbins_z, win=hybrid_gui, disable=0,live=1,pos={0,330},size={0,0},bodyWidth=80,fsize=14,title="Number of bins for I(Z) histogram",value=ghy_nbins_z
		SetVariable hy_input_range_x, disable=0,live=1,pos={0,475},size={0,0},bodyWidth=80,fsize=14,title="Result histogram range (X) user unit",value=ghy_range_x
		SetVariable hy_input_nncon_x, disable=0,live=1,pos={0,500},size={0,0},bodyWidth=80,fsize=14,title="Result histogram number of bins (X)",value=ghy_nncon_x
		SetVariable hy_input_range_z, disable=0,live=1,pos={0,525},size={0,0},bodyWidth=80,fsize=14,title="Result histogram range (Z) user unit",value=ghy_range_z
		SetVariable hy_input_nncon_z, disable=0,live=1,pos={0,550},size={0,0},bodyWidth=80,fsize=14,title="Result histogram number of bins (Z)",value=ghy_nncon_z	
	Endif
	If(popNum<3)
		Button hy_input_sestudy,disable=0,pos={340,210},size={160,30},fsize=14,proc=hy_sestudy,title="Slope error study"
		Button hy_input_longi,disable=0,pos={340,245},size={160,30},fsize=14,proc=hy_longi,title="longitudinal profiles (nf)"
	Else
		Button hy_input_sestudy,disable=2,pos={340,210},size={160,30},fsize=14,proc=hy_sestudy,title="Slope error study"
		Button hy_input_longi,disable=2,pos={340,245},size={160,30},fsize=14,proc=hy_longi,title="longitudinal profiles (nf)"			
	Endif
End

Function hy_updategui_calcType(ctrlName,popNum,popStr) : PopupMenuControl
	String ctrlName
	Variable popNum	// which item is currently selected (1-based)
	String popStr		// contents of current popup item as string
	NVAR ghy_calcType,ghy_usemirrorfile,ghy_nf
	ghy_calcType = popNum
	If(popNum>1)
		SetVariable hy_input_focallength, win=hybrid_gui, disable=0,live=1,pos={0,145},size={0,0},bodyWidth=80,fsize=14,title="Focal length (use SIMAGE if <0)",value=ghy_focallength
		PopupMenu/Z hy_input_nearfield,disable=0,live=1,pos={0,245},size={0,0},bodyWidth=80,fsize=14,title="Near-field calculation",mode=1,popvalue=StringFromList(ghy_nf,"No;YES"),value="No;YES",proc=hy_updategui_ghy_nf
		Button hy_input_longi,disable=0,pos={340,245},size={160,30},fsize=14,proc=hy_longi,title="longitudinal profiles (nf)"
	Else
		SetVariable hy_input_focallength, win=hybrid_gui, disable=2,live=1,pos={0,145},size={0,0},bodyWidth=80,fsize=14,title="Focal length (use SIMAGE if <0)",value=ghy_focallength
		PopupMenu/Z hy_input_nearfield,disable=2,live=1,pos={0,245},size={0,0},bodyWidth=80,fsize=14,title="Near-field calculation",mode=1,popvalue=StringFromList(ghy_nf,"No;YES"),value="No;YES",proc=hy_updategui_ghy_nf
		Button hy_input_longi,disable=2,pos={340,245},size={160,30},fsize=14,proc=hy_longi,title="longitudinal profiles (nf)"
	Endif
	If((popNum==3)||(popNum==4))
		SetVariable hy_input_mirrorfile, win=hybrid_gui, disable=0,live=1,pos={0,195},size={0,0},bodyWidth=160,fsize=14,title="Mirror figure error file",value=ghy_mirrorfile
		PopupMenu/Z hy_input_mirrorwave, win=hybrid_gui,disable=0,live=1,pos={0,220},size={0,0},bodyWidth=120,fsize=14,title="        Or, select wave",mode=1,popvalue=StringFromList(ghy_usemirrorfile-1,sh_popwave()),value=sh_popwave()
		Button hy_input_sestudy,disable=0,pos={340,210},size={160,30},fsize=14,proc=hy_sestudy,title="Slope error study"
	else
		SetVariable hy_input_mirrorfile, win=hybrid_gui, disable=2,live=1,pos={0,195},size={0,0},bodyWidth=160,fsize=14,title="Mirror figure error file",value=ghy_mirrorfile
		PopupMenu/Z hy_input_mirrorwave, win=hybrid_gui,disable=2,live=1,pos={0,220},size={0,0},bodyWidth=120,fsize=14,title="        Or, select wave",mode=1,popvalue=StringFromList(ghy_usemirrorfile-1,sh_popwave()),value=sh_popwave()
		Button hy_input_sestudy,disable=2,pos={340,210},size={160,30},fsize=14,proc=hy_sestudy,title="Slope error study"
	endif
	NVAR/Z ghy_regist
	If(ghy_calcType != ghy_regist || WaveExists(yp_screen)!=1)
		Button hy_input_rerun,win=hybrid_gui,disable=2,pos={340,45},size={160,30},fsize=16,proc=hy_rerun,title="Rerun (no file load)"
	Else
		Button hy_input_rerun,win=hybrid_gui,disable=0,pos={340,45},size={160,30},fsize=16,proc=hy_rerun,title="Rerun (no file load)"
	Endif
End

//Hybrid main function
Function hy_run(hy_input_run) : ButtonControl
	String hy_input_run
	NVAR ghy_diff_plane, ghy_nf
	
	//running block
	hy_readfiles()	//Read shadow output files needed by HYBRID
	hy_init()		//Calculate functions needed to construct exit pupil function
	hy_prop()	//Perform wavefront propagation 
	hy_conv()	//Perform ray resampling
	
	//output block
	print "|||||||||||||||||||||||||||||||||HYBRID OUTPUTS|||||||||||||||||||||||||||||||||||"
	switch(ghy_diff_plane)
		case 1:
			print "Generated far-field profile: xx_image_ff_histo"
			If(ghy_nf==1)
				print "Generated near-field profile: xx_image_nf_histo"
			endif
			break
		case 2:
			print "Generated far-field profile: zz_image_ff_histo"
			If(ghy_nf==1)
				print "Generated near-field profile: zz_image_nf_histo"
			endif		
			break
		case 3:
			print "Generated far-field 2D profile: xx_image_ffzz_image_ff"
			break
	endswitch

	//something needed for rerun hybrid
	NVAR ghy_calcType
	variable/G ghy_regist = ghy_calcType
	Button hy_input_rerun,win=hybrid_gui,disable=0,pos={340,45},size={160,30},fsize=16,proc=hy_rerun,title="Rerun (no file load)"
End


//Rerun hybrid without loading SHADOW files
Function hy_rerun(hy_input_rerun) : ButtonControl
	String hy_input_rerun
	print "|||||||||||||||||||||||||||||||||HYBRID RERUN|||||||||||||||||||||||||||||||||||||||||"
	hy_init()		//Calculate functions needed to construct exit pupil function
	hy_prop()	//Perform wavefront propagation 
	hy_conv()	//Perform ray resampling
	
	NVAR ghy_diff_plane, ghy_nf
	switch(ghy_diff_plane)
		case 1:
			print "Generated far-field profile: xx_image_ff_histo"
			If(ghy_nf==1)
				print "Generated near-field profile: xx_image_nf_histo"
			endif
			break
		case 2:
			print "Generated far-field profile: zz_image_ff_histo"
			If(ghy_nf==1)
				print "Generated near-field profile: zz_image_nf_histo"
			endif		
			break
		case 3:
			print "Generated far-field 2D profile: xx_image_ffzz_image_ff"
			break
	endswitch
End

//Read shadow output files needed by HYBRID
Function hy_readfiles()
	NVAR/Z ghy_n_oe,ghy_n_screen,ghy_diff_plane,ghy_calcType,ghy_nbins_x,ghy_nbins_z,ghy_npeak,ghy_usemirrorfile,ghy_lengthunit,ghy_nf
	SVAR/Z ghy_path,ghy_mirrorfile
	string str_n_oe,str_n_screen,fileShadowScreen, fileShadowAngle,fileShadowEnd,fileShadowMirr,fileShadowPresurface,fileShadowStar
	string/G gfile
	string shname,colname
	NewPath/O/Q shadow, ghy_path
	
	print "|||||||||||||||||||||||||||||||||HYBRID INPUTS|||||||||||||||||||||||||||||||||||||||||"
	str_n_oe = num2str(ghy_n_oe)
	If(ghy_n_oe<10)
		str_n_oe = "0"+str_n_oe
	endif
	str_n_screen = num2str(ghy_n_screen)
	If(ghy_n_screen<10)
		str_n_screen = "0"+str_n_screen
	endif	
	If(ghy_n_oe==0)
		fileShadowScreen = "begin.dat"
		fileShadowStar = "begin.dat"
	else
		fileShadowStar = "star."+str_n_oe
		If(ghy_n_screen==0)
			fileShadowScreen = "star."+str_n_oe
		else
			fileShadowScreen = "screen."+str_n_oe+str_n_screen
		endif
	endif
	fileShadowAngle = "angle."+str_n_oe
	fileShadowEnd = "end."+str_n_oe
	fileShadowMirr = "mirr."+str_n_oe
	fileShadowPresurface = ghy_mirrorfile
	
	//some file and parameter checks
	gfile=sh_read_gfile(ghy_path+fileShadowEnd)
	if(ghy_n_oe!=0)
		If(NumberByKey("N_SCREEN",gfile)<1)
			abort "At least one screen must exist. Found:"+StringByKey("N_SCREEN",gfile)
		endif
	endif
	If(ghy_calcType>1)	//Cases other than simple aperture
		string SL_DIS_name = "SL_DIS("+num2str(ghy_n_screen)+")"
		if(NumberByKey(SL_DIS_name,gfile)>1e-8)
			abort "The aperture screen must be placed at ZERO distance from o.e. Found at distance:"+StringByKey(SL_DIS_name,gfile)
		endif
	endif
	if((ghy_calcType==3)||(ghy_calcType==4))	//Mirror or grating with figure errors		//xshi2017
		if(NumberByKey("F_ANGLE",gfile)!=1)
			abort "File with angles not created: "+fileShadowAngle
		endif
	endif
	//read shadow image file
	sh_readsh(ghy_path+fileShadowStar,1,"shstar")
	wave shstar
	sh_getshcol(shstar,1,0,"xx_star")
	sh_getshcol(shstar,3,0,"zz_star")
	variable/G ghy_z_min, ghy_z_max, ghy_x_min, ghy_x_max
	
	//read shadow screen file
	sh_readsh(ghy_path+fileShadowScreen,1,"shscreen")
	wave shscreen
	sh_getshcol(shscreen,11,0,"wenergy")
	sh_getshcol(shscreen,19,0,"wwavelength")
	sh_getshcol(shscreen,4,0,"xp_screen")
	sh_getshcol(shscreen,5,0,"yp_screen")
	sh_getshcol(shscreen,6,0,"zp_screen")
	sh_getshcol(shscreen,23,0,"ref_screen")
	variable/G genergy = mean(wenergy)			//average photon energy in eV
	print "Using MEAN photon energy [eV]:",genergy
	wave xp_screen,yp_screen,zp_screen,ref_screen
	sh_getshcol(shscreen,1,0,"xx_screen")
	wavestats/q/z xx_screen
	ghy_x_min = v_min
	ghy_x_max = v_max
	sh_getshcol(shscreen,3,0,"zz_screen")
	wavestats/q/z zz_screen
	ghy_z_min = v_min
	ghy_z_max = v_max
	duplicate/O xp_screen dx_ray
	dx_ray = atan(xp_screen/yp_screen)		// calculate divergence from direction cosines from SHADOW file  dx = atan(v_x/v_y)
	duplicate/O zp_screen dz_ray
	dz_ray = atan(zp_screen/yp_screen)	// calculate divergence from direction cosines from SHADOW file  dz = atan(v_z/v_y)

	//Process mirror
	//reads file with mirror height mesh
 	//calculates the function of the "incident angle" and the "mirror height" versus the Z coordinate in the screen. 
 	If((ghy_calcType==3)||(ghy_calcType==4))				//xshi2017
		sh_readsh(ghy_path+fileShadowMirr,1,"shmirr")
		wave shmirr
		sh_getshcol(shmirr,1,0,"xx_mirr")
		sh_getshcol(shmirr,2,0,"yy_mirr")	

		//read in angle files
		sh_readangle(ghy_path+fileShadowAngle,1)
		wave angle_flag, angle_index, angle_inc, angle_ref
		angle_inc = (90.0 - angle_inc)/180.0*1e3*pi 
		wavestats/q/z angle_inc
		variable/G ghy_grazingangle = v_avg
		
		If(ghy_calcType==4)		//xshi2017
			angle_ref = (90.0 - angle_ref)/180.0*1e3*pi 
			wavestats/q/z angle_ref
			variable/G ghy_refangle = v_avg
		endif
		
		//read in mirror surface
		If(ghy_usemirrorfile==1&&strlen(fileShadowPresurface)!=0)
			sh_readsurface(ghy_path+fileShadowPresurface,"wmirror")
			wave wmirror
		else
			ControlInfo /W=hybrid_gui hy_input_mirrorwave
			ghy_usemirrorfile = V_Value
			string mirrorwavename = S_value
			wave mirrorwave = $S_value
			duplicate/O/D mirrorwave wmirror
			print "mirror surface loaded from wave:", mirrorwavename
		endif
		
		//generate theta(z) and l(z) curve over a continuous grid 
		variable hy_npoly_angle = 3
		variable hy_fit_npts = 1001
		variable hy_npoly_l = 6	
		CurveFit/Q/L=(hy_fit_npts) /NTHR=0 poly hy_npoly_angle,  angle_inc /X=xx_screen /D
		wave fit_angle_inc
		duplicate/O fit_angle_inc wangle_x
		CurveFit/Q/L=(hy_fit_npts) /NTHR=0 poly hy_npoly_angle,  angle_inc /X=zz_screen /D
		duplicate/O fit_angle_inc wangle_z
		
		If(ghy_calcType==4)		//xshi2017
			CurveFit/Q/L=(hy_fit_npts) /NTHR=0 poly hy_npoly_angle,  angle_ref /X=xx_screen /D
			wave fit_angle_ref
			duplicate/O fit_angle_ref wangle_ref_x
			CurveFit/Q/L=(hy_fit_npts) /NTHR=0 poly hy_npoly_angle,  angle_ref /X=zz_screen /D
			duplicate/O fit_angle_ref wangle_ref_z				
		endif
		CurveFit/Q/L=(hy_fit_npts) /NTHR=0 poly hy_npoly_l,  xx_mirr /X=xx_screen /D
		wave fit_xx_mirr
		duplicate/O fit_xx_mirr wlx		
		CurveFit/Q/L=(hy_fit_npts) /NTHR=0 poly hy_npoly_l,  yy_mirr /X=zz_screen /D
		wave fit_yy_mirr
		duplicate/O fit_yy_mirr wlz
		
		killwaves/z angle_flag, angle_index, angle_ref		//xshi2017
	endif
	
	killwaves/z W_coef,w_sigma,W_ParamConfidenceInterval,fit_yy_mirr,fit_angle_inc,fit_xx_mirr,shmirr,fit_angle_ref

End

//Calculate functions needed to construct exit pupil function
Function hy_init()
	NVAR/Z ghy_diff_plane,ghy_calcType,ghy_focallength,ghy_distance,ghy_n_oe,ghy_nbins_x,ghy_nbins_z,ghy_lengthunit
	SVAR/Z gfile
	wave/Z wmirror,angle_inc,xx_screen,zz_screen,ref_screen,xx_mirr,yy_mirr,wwavelength,dx_ray,dz_ray
	
	If(ghy_calcType>1)
		If(ghy_focallength<0)
			ghy_focallength = NumberByKey("SIMAG",gfile)
			Print "Focal length not set (<-1), take from SIMAG", ghy_focallength
		endif
		If(ghy_focallength!= NumberByKey("SIMAG",gfile))
			Print "Defined focal length is different from SIMAG, used the defined focal length = ",ghy_focallength
		else
			Print "Focal length = ",ghy_focallength
		endif			
	endif
	
	switch(ghy_diff_plane)												
		case 1:
			duplicate/O xx_screen, xx_focal_ray		// calculate position at the focal length of the OE.
			xx_focal_ray+=ghy_focallength*tan(dx_ray)	
			break
		case 2:
			duplicate/O zz_screen, zz_focal_ray		// calculate position at the focal length of the OE.
			zz_focal_ray+=ghy_focallength*tan(dz_ray)	
			break
		case 3:
			//needed when 2d near field calculation is done.
			//duplicate/O xx_screen, xx_focal_ray		// calculate position at the focal length of the OE.
			//xx_focal_ray+=ghy_focallength*tan(dx_ray)	
			//duplicate/O zz_screen, zz_focal_ray		// calculate position at the focal length of the OE.
			//zz_focal_ray+=ghy_focallength*tan(dz_ray)	
			break
	endswitch
	
	If(ghy_distance<0)
		If(ghy_n_oe!=0)
			ghy_distance = NumberByKey("T_IMAGE",gfile)
			Print "Distance not set (<-1), take from T_IMAGE", ghy_distance
		endif
	endif
	if(ghy_n_oe!=0)
		If(ghy_distance!= NumberByKey("T_IMAGE",gfile))
			Print "Defined OE star plane distance is different from T_IMAGE, used the defined distance = ",ghy_distance
		else
			Print "Propagation distance = ",ghy_distance
		endif	
	endif
	
	//Extract 1d mirror profile for 1d calculation
	If((ghy_calcType==3)||(ghy_calcType==4))	// mirror with figure error		//xshi
		If(WaveDims(wmirror)==2)
			If(ghy_diff_plane==1)
				Make/O/D/N=(dimsize(wmirror,0)) wmirror_lx
				setscale/P x, dimoffset(wmirror,0),dimdelta(wmirror,0),"",wmirror_lx
				wmirror_lx = wmirror[p][round(dimsize(wmirror,1)/2)]
			endif
			If(ghy_diff_plane==2)
				Make/O/D/N=(dimsize(wmirror,1)) wmirror_lz
				setscale/P x, dimoffset(wmirror,1),dimdelta(wmirror,1),"",wmirror_lz
				wmirror_lz = wmirror[round(dimsize(wmirror,0)/2)][p]					
			endif
		elseif(WaveDims(wmirror)==1)
			If(ghy_diff_plane==3)
				abort "2D surface profile needed for the 2D calculation."
			endif
			If(ghy_diff_plane==1)
				duplicate/O/D wmirror wmirror_lx
			endif	
			If(ghy_diff_plane==2)
				duplicate/O/D wmirror wmirror_lz
			endif	
		else
			abort "Surface profile not valid, either load SHADOW waviness format, or select a 1D or 2D Igor wave."
		endif
	endif
	
	//generate intensity profile (histogram): I_ray(z) curve
	switch(ghy_diff_plane)												
		case 1:	//1d in x
			If(ghy_nbins_x<0)		// number of bins control
				ghy_nbins_x = 200
			endif		
			ghy_nbins_x = min(ghy_nbins_x,round(dimsize(xx_screen,0)/20))
			sh_1dhist(ghy_nbins_x,"xx_screen",1,5,1,0,1,"ref_screen")
			wave xx_screen_histo
			duplicate/O xx_screen_histo wIray_x
		break
		case 2:	//1d in z
			If(ghy_nbins_z<0)		// number of bins control
				ghy_nbins_z = 200
			endif	
			ghy_nbins_z = min(ghy_nbins_z,round(dimsize(zz_screen,0)/20))
			sh_1dhist(ghy_nbins_z,"zz_screen",1,5,1,0,0,"ref_screen")	
			wave zz_screen_histo
			duplicate/O zz_screen_histo wIray_z
		break
		case 3:	//2d
			If(ghy_nbins_x<0)		// number of bins control
				ghy_nbins_x = 50
			endif
			If(ghy_nbins_z<0)		// number of bins control
				ghy_nbins_z = 50
			endif
			ghy_nbins_x = min(ghy_nbins_x,round(sqrt(dimsize(xx_screen,0)/10)))
			ghy_nbins_z = min(ghy_nbins_z,round(sqrt(dimsize(zz_screen,0)/10)))
			sh_2dhist(ghy_nbins_x,ghy_nbins_z,"xx_screen","zz_screen",1,5,1,0,0,0,0,"ref_screen")
			wave xx_screenzz_screen,xx_screenzz_screenx,xx_screenzz_screenz
			duplicate/O xx_screenzz_screen wIray_2d
			duplicate/O xx_screenzz_screenx wIray_x
			duplicate/O xx_screenzz_screenz wIray_z
		break
	endswitch	

	variable/G gwavelength = mean(wwavelength)		// in A
	switch(ghy_lengthunit)	// change wavelength unit from A	to user unit				
		case 1:
			gwavelength*=1e-8
			break
		case 2:
			gwavelength*=1e-7
			break
	endswitch
	print "Using MEAN photon wavelength ("+StringFromList(ghy_lengthunit-1, "cm;mm")+"):",gwavelength
	variable/G gknum = 2.0*pi/gwavelength        //in [user-unit]^-1, wavenumber	
	
	killwaves/z xx_screen_histo,zz_screen_histo,xx_screenzz_screen,xx_screenzz_screenx,xx_screenzz_screenz
End

//Perform wavefront propagation 
Function hy_prop()
	NVAR/Z ghy_diff_plane,ghy_calcType,ghy_focallength,ghy_distance,ghy_npeak,ghy_nf,ghy_fftnpts,ghy_scalefactor
	NVAR/Z ghy_z_min, ghy_z_max, ghy_x_min, ghy_x_max,genergy, gwavelength, gknum,ghy_nf_only, ghy_grazingangle,ghy_refangle
	wave/Z wmirror,wmirror_lx,wmirror_lz,wangle_z,wangle_x,wlz,wlx,wIray_2d,wIray_x,wIray_z,wangle_ref_x,wangle_ref_z
	
	variable fftsize,imagesize,imagenpts,focallength_ff,fftsize_x,fftsize_z,scalex,scalez,imagesize_z,imagesize_x,imagenpts_x,imagenpts_z,rmsslope
	
	// set distance and focal length for the aperture propagation.
	If(ghy_calcType == 1)
		switch(ghy_diff_plane)												
			case 1:
				ghy_focallength = (ghy_x_max-ghy_x_min)^2/gwavelength/ghy_npeak
				break
			case 2:
				ghy_focallength = (ghy_z_max-ghy_z_min)^2/gwavelength/ghy_npeak
				break
			case 3:
				ghy_focallength = (max((abs(ghy_x_max-ghy_x_min)),(abs(ghy_z_max-ghy_z_min))))^2/gwavelength/ghy_npeak
				break
		endswitch
		print  "Focal length set to:", ghy_focallength		
	endif 
	
	// automatic control of number of peaks to avoid numerical overflow.
	If(ghy_diff_plane==3)
		If(ghy_npeak<0)		// number of bins control
			ghy_npeak = 10
		endif
		ghy_npeak = min(ghy_npeak,10)
	else
		If(ghy_npeak<0)		// number of bins control
			ghy_npeak = 50
		endif
//		ghy_npeak = min(ghy_npeak,50)
	endif
	ghy_npeak = max(ghy_npeak,5)
	If(ghy_fftnpts<0)		// number of bins control
		ghy_fftnpts = 4e6
	endif
	ghy_fftnpts = min(ghy_fftnpts,4e6)
	variable scale_factor = ghy_scalefactor	//xshi Dec19
	switch(ghy_diff_plane)										
		case 1:	//1d calculation in x direction
			if(ghy_nf_only !=1)	//far field calculation
				//focallength_ff = (min(abs(ghy_x_max),abs(ghy_x_min))*2)^2/ghy_npeak/2/0.88/gwavelength		// automatically choose propagation distance
				focallength_ff = (ghy_x_max-ghy_x_min)^2/ghy_npeak/2/0.88/gwavelength		// automatically choose propagation distance
				if(ghy_calcType==3)
					rmsslope = hy_findrmsslopefromheight("wmirror_lx",0)
					//focallength_ff = min(focallength_ff, (min(abs(ghy_x_max),abs(ghy_x_min))*2)/8/rmsslope/sin(ghy_grazingangle/1e3))	// make sure the range is enough for big slope error
					focallength_ff = min(focallength_ff, (ghy_x_max-ghy_x_min)/16/rmsslope/sin(ghy_grazingangle/1e3))	// make sure the range is enough for big slope error
				endif
				if(ghy_calcType==4)		//xshi2017
					rmsslope = hy_findrmsslopefromheight("wmirror_lx",0)
					//focallength_ff = min(focallength_ff, (min(abs(ghy_x_max),abs(ghy_x_min))*2)/8/rmsslope/sin(ghy_grazingangle/1e3))	// make sure the range is enough for big slope error
					focallength_ff = min(focallength_ff, (ghy_x_max-ghy_x_min)/8/rmsslope/(sin(ghy_grazingangle/1e3)+sin(ghy_refangle/1e3)))	// make sure the range is enough for big slope error
				endif
				fftsize = scale_factor*min(100*(ghy_x_max-ghy_x_min)^2/gwavelength/focallength_ff/0.88,ghy_fftnpts)		// 100 points within fwhm of the peak
				make/C/O/N=(fftsize) wplane
				SetScale/I x, ghy_x_min-(ghy_x_max-ghy_x_min)*(scale_factor-1)/2,ghy_x_max+(ghy_x_max-ghy_x_min)*(scale_factor-1)/2,"", wplane	//xshi Dec19
				wplane=cmplx(1,0)									//plane wave
				If(scale_factor ==1)	//xshi Dec19
					wplane*=sqrt(wIray_x(x))								//intensity scaling of the plane wave
				endif
				wplane*=Exp(cmplx(0,-1)*gknum*(x^2/focallength_ff)/2)		//sperical wave converging to the focal plane
				If(ghy_calcType==3)
					wplane*=Exp(cmplx(0,-1)*4*pi/gwavelength*sin(wangle_x(x)/1e3)*wmirror_lx(wlx(x)))	//add phase shift from mirror figure error 
				endif
				If(ghy_calcType==4)		//xshi2017
					wplane*=Exp(cmplx(0,-1)*2*pi/gwavelength*(sin(wangle_x(x)/1e3)+sin(wangle_ref_x(x)/1e3))*wmirror_lx(wlx(x)))	//add phase shift from mirror figure error 
				endif
				FFT/OUT=1/dest=wplane_fft wplane
				Duplicate/O/C wplane_fft mop
				mop = exp(cmplx(0,-1)*(pi*(gwavelength*focallength_ff))*(x^2))
				wplane_fft*=mop
				IFFT/C /DEST=inten wplane_fft
				setscale/P x, dimoffset(wplane,0),dimdelta(wplane,0),inten
				imagesize = min(abs(ghy_x_max),abs(ghy_x_min))*2		// ghy_npeak in the wavefront propagation image
				imagenpts = round(imagesize/dimdelta(inten,0)/2)*2+1			
				Make/O/N=(imagenpts) dif_xp							//angular diffraction profile
				setscale/I x, -(imagenpts-1)/2*dimdelta(inten,0),(imagenpts-1)/2*dimdelta(inten,0),dif_xp
				dif_xp = magsqr(inten(x))
				setscale/I x, -(imagenpts-1)/2*dimdelta(inten,0)/focallength_ff,(imagenpts-1)/2*dimdelta(inten,0)/focallength_ff,  dif_xp
			endif
			If((ghy_nf==1&&ghy_calctype>1)||ghy_nf_only==1)		// near field calculation
				fftsize = scale_factor* min(100*(ghy_x_max-ghy_x_min)^2/gwavelength/ghy_focallength/0.88,ghy_fftnpts)		// 100 points within fwhm of the peak
				make/C/O/N=(fftsize) wplane
				SetScale/I x, ghy_x_min-(ghy_x_max-ghy_x_min)*(scale_factor-1)/2,ghy_x_max+(ghy_x_max-ghy_x_min)*(scale_factor-1)/2,"", wplane	//xshi Dec19
				wplane=cmplx(1,0)									//plane wave
				If(scale_factor ==1)	//xshi Dec19
					wplane*=sqrt(wIray_x(x))								//intensity scaling of the plane wave
				endif
				wplane*=Exp(cmplx(0,-1)*gknum*(x^2/ghy_focallength)/2)	//sperical wave converging to the focal plane
				If(ghy_calcType==3)
					wplane*=Exp(cmplx(0,-1)*4*pi/gwavelength*sin(wangle_x(x)/1e3)*wmirror_lx(wlx(x)))	//add phase shift from mirror figure error 
				endif
				If(ghy_calcType==4)	//xshi2017
					wplane*=Exp(cmplx(0,-1)*2*pi/gwavelength*(sin(wangle_x(x)/1e3)+sin(wangle_ref_x(x)/1e3))*wmirror_lx(wlx(x)))	//add phase shift from mirror figure error 
				endif
				FFT/OUT=1/dest=wplane_fft wplane
				Duplicate/O/C wplane_fft mop
				mop = exp(cmplx(0,-1)*(pi*(gwavelength*ghy_distance))*(x^2))
				wplane_fft*=mop
				IFFT/C /DEST=inten wplane_fft
				setscale/P x, dimoffset(wplane,0),dimdelta(wplane,0),inten
				imagesize = (ghy_npeak*2*0.88*gwavelength*ghy_focallength/abs(ghy_x_max-ghy_x_min))	// ghy_npeak in the wavefront propagation image
				imagesize = max(imagesize,2*abs((ghy_x_max-ghy_x_min)*(ghy_distance-ghy_focallength))/ghy_focallength)
				If(ghy_calcType==3)
					rmsslope = hy_findrmsslopefromheight("wmirror_lx",0)
					imagesize = max(imagesize,16*rmsslope*ghy_focallength*sin(ghy_grazingangle/1e3))	//in case of big slope error
				endif
				If(ghy_calcType==4)	//xshi2017
					rmsslope = hy_findrmsslopefromheight("wmirror_lx",0)
					imagesize = max(imagesize,8*rmsslope*ghy_focallength*(sin(ghy_grazingangle/1e3)+sin(ghy_refangle/1e3)))	//in case of big slope error
				endif
				imagenpts = round(imagesize/dimdelta(inten,0)/2)*2+1
				Make/O/N=(imagenpts) dif_x		//diffraction profile
				setscale/I x, -(imagenpts-1)/2*dimdelta(inten,0),(imagenpts-1)/2*dimdelta(inten,0),dif_x
				dif_x = magsqr(inten(x))
			endif	
			break
		case 2: //1d calculation in z direction
			if(ghy_nf_only !=1)	//far field calculation
				//focallength_ff = (min(abs(ghy_z_max),abs(ghy_z_min))*2)^2/ghy_npeak/2/0.88/gwavelength		// automatically choose propagation distance
				focallength_ff = (ghy_z_max-ghy_z_min)^2/ghy_npeak/2/0.88/gwavelength		// automatically choose propagation distance
				if((ghy_calcType==3)||(ghy_calcType==4))		//xshi2017
					rmsslope = hy_findrmsslopefromheight("wmirror_lz",0)
					//focallength_ff = min(focallength_ff, (min(abs(ghy_z_max),abs(ghy_z_min))*2)/16/rmsslope)		// make sure the range is enough for big slope error
					focallength_ff = min(focallength_ff, (ghy_z_max-ghy_z_min)/16/rmsslope)		// make sure the range is enough for big slope error
				endif
				fftsize = scale_factor* min(100*(ghy_z_max-ghy_z_min)^2/gwavelength/focallength_ff/0.88,ghy_fftnpts)		// 100 points within fwhm of the peak
				make/C/O/N=(fftsize) wplane
				SetScale/I x, ghy_z_min-(ghy_z_max-ghy_z_min)*(scale_factor-1)/2,ghy_z_max+(ghy_z_max-ghy_z_min)*(scale_factor-1)/2,"", wplane	//xshi Dec19
				wplane=cmplx(1,0)									//plane wave
				If(scale_factor ==1)	//xshi Dec19
					wplane*=sqrt(wIray_z(x))								//intensity scaling of the plane wave
				endif
				wplane*=Exp(cmplx(0,-1)*gknum*(x^2/focallength_ff)/2)		//sperical wave converging to the focal plane
				If(ghy_calcType==3)
					wplane*=Exp(cmplx(0,-1)*4*pi/gwavelength*sin(wangle_z(x)/1e3)*wmirror_lz(wlz(x)))	//add phase shift from mirror figure error 
				endif
				If(ghy_calcType==4)		//xshi2017
					wplane*=Exp(cmplx(0,-1)*2*pi/gwavelength*(sin(wangle_z(x)/1e3)+sin(wangle_ref_z(x)/1e3))*wmirror_lz(wlz(x)))	//add phase shift from mirror figure error 
				endif
				FFT/OUT=1/dest=wplane_fft wplane
				Duplicate/O/C wplane_fft mop
				mop = exp(cmplx(0,-1)*(pi*(gwavelength*focallength_ff))*(x^2))
				wplane_fft*=mop
				IFFT/C /DEST=inten wplane_fft
				setscale/P x, dimoffset(wplane,0),dimdelta(wplane,0),inten
				imagesize = min(abs(ghy_z_max),abs(ghy_z_min))*2		// ghy_npeak in the wavefront propagation image
				imagenpts = round(imagesize/dimdelta(inten,0)/2)*2+1			
				Make/O/N=(imagenpts) dif_zp							//angular diffraction profile
				setscale/I x, -(imagenpts-1)/2*dimdelta(inten,0),(imagenpts-1)/2*dimdelta(inten,0),dif_zp
				dif_zp = magsqr(inten(x))
				setscale/I x, -(imagenpts-1)/2*dimdelta(inten,0)/focallength_ff,(imagenpts-1)/2*dimdelta(inten,0)/focallength_ff,  dif_zp
			endif
			If((ghy_nf==1&&ghy_calctype>1)||ghy_nf_only==1)				// near field calculation
				fftsize =  scale_factor*min(100*(ghy_z_max-ghy_z_min)^2/gwavelength/ghy_focallength/0.88,ghy_fftnpts)		// 100 points within fwhm of the peak
				make/C/O/N=(fftsize) wplane
				SetScale/I x, ghy_z_min-(ghy_z_max-ghy_z_min)*(scale_factor-1)/2,ghy_z_max+(ghy_z_max-ghy_z_min)*(scale_factor-1)/2,"", wplane	//xshi Dec19
				wplane=cmplx(1,0)									//plane wave
				If(scale_factor ==1)	//xshi Dec19
					wplane*=sqrt(wIray_z(x))								//intensity scaling of the plane wave
				endif
				wplane*=Exp(cmplx(0,-1)*gknum*(x^2/ghy_focallength)/2)	//sperical wave converging to the focal plane
				If(ghy_calcType==3)
					wplane*=Exp(cmplx(0,-1)*4*pi/gwavelength*sin(wangle_z(x)/1e3)*wmirror_lz(wlz(x)))	//add phase shift from mirror figure error 
				endif
				If(ghy_calcType==4)		//xshi2017
					wplane*=Exp(cmplx(0,-1)*2*pi/gwavelength*(sin(wangle_z(x)/1e3)+sin(wangle_ref_z(x)/1e3))*wmirror_lz(wlz(x)))	//add phase shift from mirror figure error 
				endif
				FFT/OUT=1/dest=wplane_fft wplane
				Duplicate/O/C wplane_fft mop
				mop = exp(cmplx(0,-1)*(pi*(gwavelength*ghy_distance))*(x^2))
				wplane_fft*=mop
				IFFT/C /DEST=inten wplane_fft
				setscale/P x, dimoffset(wplane,0),dimdelta(wplane,0),inten
				imagesize = (ghy_npeak*2*0.88*gwavelength*ghy_focallength/abs(ghy_z_max-ghy_z_min))	// ghy_npeak in the wavefront propagation image
				imagesize = max(imagesize,2*abs((ghy_z_max-ghy_z_min)*(ghy_distance-ghy_focallength))/ghy_focallength)
				If((ghy_calcType==3)||(ghy_calcType==4))
					rmsslope = hy_findrmsslopefromheight("wmirror_lz",0)
					imagesize = max(imagesize,16*rmsslope*ghy_focallength)	//in case of big slope error
				endif
				imagenpts = round(imagesize/dimdelta(inten,0)/2)*2+1
				Make/O/N=(imagenpts) dif_z		//diffraction profile
				setscale/I x, -(imagenpts-1)/2*dimdelta(inten,0),(imagenpts-1)/2*dimdelta(inten,0),dif_z
				dif_z = magsqr(inten(x))
			endif
////	some old versions
////			fftsize = min(10*(ghy_z_max-ghy_z_min)^2/gwavelength/ghy_focallength/0.88,ghy_fftnpts)		// 10 points within fwhm of the peak
////			hy_makeplanewave("wplane",1,genergy,genergy,1,0,0.01,fftsize,ghy_z_min, ghy_z_max)
////			hy_scalewaveintensity_v("wplane","wIray_z","wplane")
////			hy_propagatetoLens("wplane",ghy_focallength,ghy_focallength,"wscreen")
////			hy_propagatemirrorprofile_v("wscreen","wmirror_lz",-1,0,"wangle_z","wlz","wscreen")
////			hy_propagatefreespace("wscreen",ghy_focallength,"wscreen")
////			hy_magtointen("wscreen","inten")							// to generate the intensity profile in 2d from the 3d wave field
////			wave inteny
////			imagesize = (ghy_npeak*2*0.88*gwavelength*ghy_focallength/abs(ghy_z_max-ghy_z_min))	// ghy_npeak in the wavefront propagation image
////			imagenpts = round(imagesize/dimdelta(inteny,0)/2)*2+1
////			Make/O/N=(imagenpts) dif_zp
////			setscale/I x, -(imagenpts-1)/2*dimdelta(inteny,0),(imagenpts-1)/2*dimdelta(inteny,0),dif_zp
////			dif_zp = inteny(x)
////			setscale/I x, -(imagenpts-1)/2*dimdelta(inteny,0)/ghy_focallength,(imagenpts-1)/2*dimdelta(inteny,0)/ghy_focallength,  dif_zp
////			If(ghy_nf==1)	// near field
////				hy_propagatetoLens("wplane",ghy_focallength,ghy_focallength,"wstar")
////				hy_propagatemirrorprofile_v("wstar","wmirror_lz",-1,0,"wangle_z","wlz","wstar")
////				hy_propagatefreespace("wstar",ghy_distance,"wstar")
////				hy_magtointen("wstar","inten")
////				imagesize = max(imagesize,2*abs((ghy_z_max-ghy_z_min)*(ghy_distance-ghy_focallength))/ghy_focallength)
////				imagenpts = round(imagesize/dimdelta(inteny,0)/2)*2+1
////				Make/O/N=(imagenpts) dif_z
////				setscale/I x, -(imagenpts-1)/2*dimdelta(inteny,0),(imagenpts-1)/2*dimdelta(inteny,0),dif_z
////				dif_z = inteny(x)
////			endif		
			break
		case 3:	//2d calculation
			If(ghy_nf_only!=1)		//far field calculation
				//focallength_ff = (min(min(abs(ghy_z_max),abs(ghy_z_min)),min(abs(ghy_x_max),abs(ghy_x_min)))*2)^2/ghy_npeak/2/0.88/gwavelength	// automatically choose propagation distance
				focallength_ff = (min((ghy_z_max-ghy_z_min),(ghy_x_max-ghy_x_min)))^2/ghy_npeak/2/0.88/gwavelength	// automatically choose propagation distance
				fftsize_x = min(20*(ghy_x_max-ghy_x_min)^2/gwavelength/focallength_ff/0.88,ghy_fftnpts)		// 20 points within fwhm of the peak
				fftsize_z = min(20*(ghy_z_max-ghy_z_min)^2/gwavelength/focallength_ff/0.88,ghy_fftnpts)		// 20 points within fwhm of the peak		
				make/C/O/N=(fftsize_x,fftsize_z) wplane
				SetScale/I x, ghy_x_min,ghy_x_max,"", wplane
				SetScale/I y, ghy_z_min,ghy_z_max,"", wplane
				make/O/N=(fftsize_x,fftsize_z) wIray_2d_interpolated
				ImageInterpolate/F={((fftsize_x-1)/(dimsize(wIray_2d,0)-1)),((fftsize_z-1)/(dimsize(wIray_2d,1)-1))}/DEST=wIray_2d_interpolated Bilinear wIray_2d
	//			ImageInterpolate/F={((fftsize_x-1)/(dimsize(wIray_2d,0)-1)),((fftsize_z-1)/(dimsize(wIray_2d,1)-1))}/DEST=wIray_2d_interpolated/D=3 spline wIray_2d
				wplane=cmplx(1,0)										//plane wave
				wplane*=sqrt(wIray_2d_interpolated)							//intensity scaling of the plane wave
				wplane*=Exp(cmplx(0,-1)*gknum*((x^2+y^2)/focallength_ff)/2)	//sperical wave converging to the focal plane
				If(ghy_calcType==3)
					hy_mirror_project(wmirror,wlz,wplane)	//assuming wlx is linear with a slope of 1, so don't need to rescale the axis.
					wave wmirror_projected
					wplane*=Exp(cmplx(0,-1)*4*pi/gwavelength*sin(wangle_z(x)/1e3)*wmirror_projected)	//add phase shift from mirror figure error,  angle variation in meridinal direcion only
				endif
				If(ghy_calcType==4)		//xshi2017
					hy_mirror_project(wmirror,wlz,wplane)	//assuming wlx is linear with a slope of 1, so don't need to rescale the axis.
					wave wmirror_projected
					wplane*=Exp(cmplx(0,-1)*2*pi/gwavelength*(sin(wangle_z(x)/1e3)+sin(wangle_ref_z(x)/1e3))*wmirror_projected)	//add phase shift from mirror figure error,  angle variation in meridinal direcion only
				endif
				FFT/OUT=1/dest=wplane_fft wplane
				Duplicate/O/C wplane_fft mop
				mop = exp(cmplx(0,-1)*(pi*(gwavelength*focallength_ff))*(x^2+y^2))
				wplane_fft*=mop
				IFFT/C /DEST=inten wplane_fft
				setscale/P x, dimoffset(wplane,0),dimdelta(wplane,0),inten
				setscale/P y, dimoffset(wplane,1),dimdelta(wplane,1),inten
				imagesize_x =min(abs(ghy_x_max),abs(ghy_x_min))*2
				imagesize_x = min(imagesize_x,ghy_npeak*2*0.88*gwavelength*focallength_ff/abs(ghy_x_max-ghy_x_min))
				imagenpts_x = round(imagesize_x/dimdelta(inten,0)/2)*2+1
				imagesize_z =min(abs(ghy_z_max),abs(ghy_z_min))*2	
				imagesize_z = min(imagesize_z,ghy_npeak*2*0.88*gwavelength*focallength_ff/abs(ghy_z_max-ghy_z_min))
				imagenpts_z = round(imagesize_z/dimdelta(inten,1)/2)*2+1				
				Make/O/N=(imagenpts_x,imagenpts_z) dif_xpzp			//2d angular diffraction profile
				setscale/I x, -(imagenpts_x-1)/2*dimdelta(inten,0),(imagenpts_x-1)/2*dimdelta(inten,0),dif_xpzp
				setscale/I y, -(imagenpts_z-1)/2*dimdelta(inten,1),(imagenpts_z-1)/2*dimdelta(inten,1),dif_xpzp
				dif_xpzp = magsqr(inten(x)(y))
				setscale/I x, -(imagenpts_x-1)/2*dimdelta(inten,0)/focallength_ff,(imagenpts_x-1)/2*dimdelta(inten,0)/focallength_ff,dif_xpzp
				setscale/I y, -(imagenpts_z-1)/2*dimdelta(inten,1)/focallength_ff,(imagenpts_z-1)/2*dimdelta(inten,1)/focallength_ff,dif_xpzp
			endif		
////	some near field 2d calculation 			
////			focallength_ff = (min(min(abs(ghy_z_max),abs(ghy_z_min)),min(abs(ghy_x_max),abs(ghy_x_min)))*2)^2/ghy_npeak/2/0.88/gwavelength
////			fftsize_x = min(10*(ghy_x_max-ghy_x_min)^2/gwavelength/focallength_ff/0.88,ghy_fftnpts)		// 10 points within fwhm of the peak
////			fftsize_z = min(10*(ghy_z_max-ghy_z_min)^2/gwavelength/focallength_ff/0.88,ghy_fftnpts)		// 10 points within fwhm of the peak
////			make/C/O/N=(floor(dimsize(wIray_2d,0)/2)*2,floor(dimsize(wIray_2d,1)/2)*2) wplane
////			SetScale/P x, dimoffset(wIray_2d,0),dimdelta(wIray_2d,0), wplane
////			SetScale/P y, dimoffset(wIray_2d,1),dimdelta(wIray_2d,1), wplane
////			wplane = cmplx(sqrt(wIray_2d[p][q]),0)
////			wplane*=Exp(cmplx(0,-1)*gknum*((x^2/focallength_ff)+(y^2/focallength_ff))/2)
////			FFT/OUT=1/dest=test_fft1/COLS wplane
////			scalex = round(fftsize_x/dimsize(test_fft1,0))
////			make/O/C/N=((dimsize(test_fft1,0)-1)*scalex+1,dimsize(test_fft1,1)) mop
////			SetScale/I x, -abs(dimdelta(test_fft1,0)*(dimsize(test_fft1,0)-1)*scalex/2),abs(dimdelta(test_fft1,0)*(dimsize(test_fft1,0)-1)*scalex/2),"",   mop
////			SetScale/P y, DimOffset(test_fft1,1),DimDelta(test_fft1,1),"",   mop
////			mop =cmplx(0,0)	
////			mop[ceil((dimsize(mop,0)-dimsize(test_fft1,0))/2),floor((dimsize(mop,0)+dimsize(test_fft1,0))/2)-1][] = test_fft1(x)[q]*exp(cmplx(0,-1)*(pi*(gwavelength*focallength_ff))*(x^2))
////			IFFT/C/COLS/DEST=wfout mop
////			make/N=(dimsize(wfout,0))/D/O tmp
////			setscale/P x, dimoffset(wfout,0), dimdelta(wfout,0),"",tmp
////			tmp=sqrt(magsqr(wfout[p](0)))
////			wavestats/q/z tmp
////			setscale/P x, -V_maxloc,dimdelta(wfout,0),"",wfout
////			imagesize = min((ghy_npeak*2*0.88*gwavelength*focallength_ff/abs(ghy_x_max-ghy_x_min)),(dimsize(wfout,0)-1)*dimdelta(wfout,0))
////			imagenpts = round(imagesize/dimdelta(wfout,0)/2)*2+1			
////			make/O/C/N=(imagenpts,dimsize(wfout,1)) test_1
////			setscale/I x,-(imagenpts-1)/2*dimdelta(wfout,0),(imagenpts-1)/2*dimdelta(wfout,0),"",test_1
////			setscale/P y, dimoffset(wfout,1),dimdelta(wfout,1),"",test_1
////			test_1 =wfout(x)[q]
////			FFT/OUT=1/dest=test_fft2/ROWS test_1
////			scalez = round(fftsize_z/dimsize(test_fft1,1))
////			make/O/C/N=(dimsize(test_fft2,0),(dimsize(test_fft2,1)-1)*scalez+1) mop2
////			SetScale/P x, DimOffset(test_fft2,0),DimDelta(test_fft2,0),"",   mop2
////			SetScale/I y,  -abs(dimdelta(test_fft2,1)*(dimsize(test_fft2,1)-1)*scalez/2),abs(dimdelta(test_fft2,1)*(dimsize(test_fft2,1)-1)*scalez/2),"",mop2
////			mop2 =cmplx(0,0)		
////			mop2[][(ceil(dimsize(mop2,1)-dimsize(test_fft2,1))/2),floor((dimsize(mop2,1)+dimsize(test_fft2,1))/2)-1]= test_fft2[p](y)*exp(cmplx(0,-1)*(pi*(gwavelength*focallength_ff))*(y^2))
////			IFFT/C/ROWS/DEST=wfout2 mop2
////			make/N=(dimsize(wfout2,1))/D/O tmp
////			setscale/P x, dimoffset(wfout2,1), dimdelta(wfout2,1),"",tmp
////			tmp=sqrt(magsqr(wfout2(0)[p]))
////			wavestats/q/z tmp
////			setscale/P y, -V_maxloc,dimdelta(wfout2,1),"",wfout2
////			imagesize = min((ghy_npeak*2*0.88*gwavelength*focallength_ff/abs(ghy_z_max-ghy_z_min)),(dimsize(wfout2,1)-1)*dimdelta(wfout2,1))
////			imagenpts = round(imagesize/dimdelta(wfout2,1)/2)*2+1			
////			make/O/N=(dimsize(wfout2,0),imagenpts) image
////			setscale/P x, dimoffset(wfout2,0)/focallength_ff,dimdelta(wfout2,0)/focallength_ff,"",image
////			setscale/I y,-(imagenpts-1)/2*dimdelta(wfout2,1),(imagenpts-1)/2*dimdelta(wfout2,1),"",image
////			image = magsqr(wfout2[p](y))
////			setscale/I y,-(imagenpts-1)/2*dimdelta(wfout2,1)/focallength_ff,(imagenpts-1)/2*dimdelta(wfout2,1)/focallength_ff,"",image
			If((ghy_nf==1&&ghy_calctype>1)||ghy_nf_only==1)	// near field
				doalert 0, "2d near field not available yet, only far field is calculated"
			endif
			break
	endswitch
	
	If(ghy_calctype==1)												
		ghy_focallength = -1
	endif
	killwaves/z wplane, wIray_2d_interpolated,wmirror_projected,wplane_fft,mop,inten
End

//Perform ray resampling
Function hy_conv()
	NVAR/Z ghy_diff_plane,ghy_calcType,ghy_focallength,ghy_distance,ghy_npeak,ghy_nf
	NVAR/Z ghy_range_x,ghy_range_z,ghy_nncon_x,ghy_nncon_z	
	wave/Z xx_screen,zz_screen,xp_screen,yp_screen,zp_screen,ref_screen,xx_focal_ray, zz_focal_ray
	wave/Z dif_xp,dif_x,dif_zp,dif_z,dif_xz,dif_xpzp,dx_ray,dz_ray
	variable nbins
	nbins = ghy_npeak*20+1			//at least 10 bins in each peak
	switch(ghy_diff_plane)												
		case 1:	//1d in x direction
			hy_createCDF1D("dif_xp")		//create cumulative distribution function from the angular diffraction profile
			hy_MakeDist1D("xp_screen")	//generate random ray divergence kicks based on the CDF, the number of rays is the same as in the original shadow file
			wave pos_dif
			duplicate/O pos_dif dx_wave
			dx_wave = atan(pos_dif)		// calculate dx from tan(dx)
			duplicate/O dx_ray, dx_conv
			dx_conv += dx_wave			// add the ray divergence kicks
			duplicate/O xx_screen xx_image_ff
			xx_image_ff += ghy_distance*tan(dx_conv)		//ray tracing to the image plane
			If(ghy_range_x<0||ghy_nncon_x<2)		//make plots
				sh_1dhist(nbins,"xx_image_ff",1,5,1,0,0,"ref_screen")
			else
				sh_1dhist(ghy_nncon_x,"xx_image_ff",2,5,1,-ghy_range_x/2,ghy_range_x/2,"ref_screen")
			endif
			If(ghy_nf==1&&ghy_calctype>1)	// near field
				hy_createCDF1D("dif_x")
				hy_MakeDist1D("xx_focal_ray")	
				wave pos_dif		
				duplicate/O pos_dif xx_wave
				duplicate/O xx_focal_ray xx_image_nf
				xx_image_nf += xx_wave
				If(ghy_range_x<0||ghy_nncon_x<2)
					sh_1dhist(nbins,"xx_image_nf",1,5,1,0,0,"ref_screen")
				else
					sh_1dhist(ghy_nncon_x,"xx_image_nf",2,5,1,-ghy_range_x/2,ghy_range_x/2,"ref_screen")
				endif
			endif
			break
		case 2:	//1d in z direction
		////make a if (ghy_longi == 1)
			hy_createCDF1D("dif_zp")		//create cumulative distribution function from the angular diffraction profile
			hy_MakeDist1D("zp_screen")	//generate random ray divergence kicks based on the CDF, the number of rays is the same as in the original shadow file
			wave pos_dif
			duplicate/O pos_dif dz_wave
			dz_wave = atan(pos_dif)		// calculate dz from tan(dz)
			
			duplicate/O dz_ray, dz_conv
			dz_conv += dz_wave			// add the ray divergence kicks
			duplicate/O zz_screen zz_image_ff
			zz_image_ff += ghy_distance*tan(dz_conv)		//ray tracing to the image plane
			
			If(ghy_range_z<0||ghy_nncon_z<2)
				sh_1dhist(nbins,"zz_image_ff",1,5,1,0,0,"ref_screen")
			else
				sh_1dhist(ghy_nncon_z,"zz_image_ff",2,5,1,-ghy_range_z/2,ghy_range_z/2,"ref_screen")
			endif
		///endif here
			If(ghy_nf==1&&ghy_calctype>1)	// near field
				hy_createCDF1D("dif_z")
				hy_MakeDist1D("zz_focal_ray")	
				wave pos_dif	
				duplicate/O pos_dif zz_wave
				duplicate/O zz_focal_ray zz_image_nf
				zz_image_nf += zz_wave
				If(ghy_range_z<0||ghy_nncon_z<2)
					sh_1dhist(nbins,"zz_image_nf",1,5,1,0,0,"ref_screen")
				else
					sh_1dhist(ghy_nncon_z,"zz_image_nf",2,5,1,-ghy_range_z/2,ghy_range_z/2,"ref_screen")
				endif
			endif
			break
		case 3:	//2d calculation
			hy_createCDF2D("dif_xpzp")	//create 2d cumulative distribution function from the angular diffraction profile
			hy_MakeDist2D("zp_screen")	//generate random ray divergence kicks based on the CDF, the number of rays is the same as in the original shadow file
			wave xDiv,zDiv
			duplicate/O xDiv dx_wave
			dx_wave = atan(xDiv)
			duplicate/O dx_ray, dx_conv
			dx_conv += dx_wave
			duplicate/O xx_screen xx_image_ff
			xx_image_ff += ghy_distance*tan(dx_conv)	
			duplicate/O zDiv dz_wave
			dz_wave = atan(zDiv)
			duplicate/O dz_ray, dz_conv
			dz_conv += dz_wave
			duplicate/O zz_screen zz_image_ff
			zz_image_ff += ghy_distance*tan(dz_conv)	
			If(ghy_range_z<0||ghy_range_x<0||ghy_nncon_x<2||ghy_nncon_z<2)
				sh_2dhist(nbins,nbins,"xx_image_ff","zz_image_ff",1,5,1,0,0,0,0,"ref_screen")
			else
				sh_2dhist(ghy_nncon_x,ghy_nncon_z,"xx_image_ff","zz_image_ff",2,5,1,-ghy_range_x/2,ghy_range_x/2,-ghy_range_z/2,ghy_range_z/2,"ref_screen")
			endif
			break
	endswitch
	killwaves/z mDist,resu,ForVer,ForHor,zDiv,xDiv,pos_dif,dx_wave,dz_wave
End

//save shadow files for the future raytracing
Function hy_savefiles(hy_input_savefiles) : ButtonControl
	String hy_input_savefiles
	NVAR/Z ghy_n_oe,ghy_n_screen,ghy_diff_plane,ghy_calcType,ghy_distance
	SVAR ghy_path
	wave/Z shscreen,shstar, xx_screen,zz_screen,xp_screen,yp_screen,zp_screen, dx_conv,dz_conv,xx_image_ff,zz_image_ff,xx_image_nf,zz_image_nf
	string str_n_oe,str_n_screen, fscreen_hybrid, fstar_hybrid, fstar_hybrid_nf
	str_n_oe = num2str(ghy_n_oe)
	If(ghy_n_oe<10)
		str_n_oe = "0"+str_n_oe
	endif
	str_n_screen = num2str(ghy_n_screen)
	If(ghy_n_screen<10)
		str_n_screen = "0"+str_n_screen
	endif	
	If(ghy_n_oe==0)
		fscreen_hybrid = "begin_hybrid.dat"	
		fstar_hybrid = "begin_hybrid.dat"	
	else
	 	fstar_hybrid = "star_hybrid."+str_n_oe
		If(ghy_n_screen==0)
			fscreen_hybrid = "star_hybrid."+str_n_oe		
		else
			fscreen_hybrid = "screen_hybrid."+str_n_oe+str_n_screen
		endif
	endif
	switch(ghy_diff_plane)												
		case 1:	//1d in x
			duplicate/O yp_screen angle_perpen, angle_num
			angle_perpen = atan(zp_screen/yp_screen)
			angle_num = sqrt(1+tan(angle_perpen)*tan(angle_perpen)+tan(dx_conv)*tan(dx_conv))
			shscreen[3][]=tan(dx_conv[q])/angle_num[q]
			shscreen[4][]=1/angle_num[q]
			shscreen[5][]=tan(angle_perpen[q])/angle_num[q]
			sh_putrays(ghy_path+fscreen_hybrid,shscreen)
			If(stringmatch(fscreen_hybrid,fstar_hybrid)==1)
				sh_putrays(ghy_path+fstar_hybrid,shscreen)
			else
				shstar[3,5][] = shscreen[p][q]
				shstar[0][] = xx_image_ff[q]
				sh_putrays(ghy_path+fstar_hybrid,shstar)
			endif
		break
		case 2:	//1d in z
			duplicate/O yp_screen angle_perpen, angle_num
			angle_perpen = atan(xp_screen/yp_screen)
			angle_num = sqrt(1+tan(angle_perpen)*tan(angle_perpen)+tan(dz_conv)*tan(dz_conv))
			shscreen[3][]=tan(angle_perpen[q])/angle_num[q]
			shscreen[4][]=1/angle_num[q]
			shscreen[5][]=tan(dz_conv[q])/angle_num[q]
			sh_putrays(ghy_path+fscreen_hybrid,shscreen)
			If(stringmatch(fscreen_hybrid,fstar_hybrid)==1)
				sh_putrays(ghy_path+fstar_hybrid,shscreen)
			else
				shstar[3,5][] = shscreen[p][q]
				shstar[2][] = zz_image_ff[q]
				sh_putrays(ghy_path+fstar_hybrid,shstar)
			endif
		break
		case 3:	//2d
			duplicate/O yp_screen, angle_num
			angle_num = sqrt(1+tan(dx_conv)*tan(dx_conv)+tan(dz_conv)*tan(dz_conv))
			shscreen[3][]=tan(dx_conv[q])/angle_num[q]
			shscreen[4][]=1/angle_num[q]
			shscreen[5][]=tan(dz_conv[q])/angle_num[q]
			sh_putrays(ghy_path+fscreen_hybrid,shscreen)
			If(stringmatch(fscreen_hybrid,fstar_hybrid)==1)
				sh_putrays(ghy_path+fstar_hybrid,shscreen)
			else
				shstar[3,5][] = shscreen[p][q]
				shstar[0][] = xx_image_ff[q]
				shstar[2][] = zz_image_ff[q]
				sh_putrays(ghy_path+fstar_hybrid,shstar)
			endif		
		break
	endswitch
	killwaves/z angle_num,angle_perpen
End

Function hy_closeplots(hy_input_closeplots) : ButtonControl
	String hy_input_closeplots
	sh_kill_plots("hyplot")
End

//Slope error study for mirrors, 1d only
Function hy_sestudy(hy_input_sestudy) : ButtonControl
	String hy_input_sestudy
	NVAR/Z ghy_calcType,ghy_nf_only,ghy_nf,ghy_diff_plane,ghy_lengthunit,ghy_range_x,ghy_range_z,ghy_nncon_x,ghy_nncon_z
	wave/Z xx_image_ff_histo,zz_image_ff_histo,xx_image_nf_histo,zz_image_nf_histo
	variable newse,ffornf,error_type,slope_del, slope_min, slope_max, plotornot
	If(ghy_calcType<3)
		abort "Need to run hybrid with figure error once"
	endif
	newse = 0
	ffornf = 0
	slope_min = 0
	slope_max =10
	slope_del = 0.5
	error_type=1
	plotornot = 2
	Prompt newse, "New mirror surface?", popup, "No;Yes"	
	Prompt ffornf, "Calculation mode:", popup, "Far-field;Near-field;Both"
	Prompt error_type, "Figure error type", popup,"Slope;Height"
	Prompt slope_min, "Minimum error (urad or nm):"
	Prompt slope_max, "Maxinum error (urad or nm)"
	Prompt slope_del, "Step size (urad or nm)"
	Prompt plotornot,"Plot results", popup,"Yes;No"
	DoPrompt "Slope error study", newse,ffornf, error_type, slope_min, slope_max,slope_del,plotornot
	if (V_flag==1)
		return 0
	endif
	variable nn = (slope_max-slope_min)/slope_del+1
	variable nncon, halfrange_ff,halfrange_nf, mirrorlength, mirror_npts
	//backup mirror error files and check hybrid status
	If(ghy_diff_plane == 1)
		If(waveexists(xx_image_ff_histo)!=1)
			abort "Need to run HYBRID once"
		endif
		If(ghy_range_x<0||ghy_nncon_x<2)
			abort "Need to specify histogram range and bins in the Result plotting control section"
		endif
		mirrorlength = dimdelta(wmirror_lx,0)*(dimsize(wmirror_lx,0)-1)
		mirror_npts = round(dimsize(wmirror_lx,0)/2)*2
		nncon = dimsize(xx_image_ff_histo,0)
		halfrange_ff = (dimsize(xx_image_ff_histo,0)-1)*dimdelta(xx_image_ff_histo,0)/2
		halfrange_nf = (dimsize(xx_image_nf_histo,0)-1)*dimdelta(xx_image_nf_histo,0)/2
		wave wmirror_lx
		Duplicate/O wmirror_lx wmirror_lx_backup	
	elseif(ghy_diff_plane == 2)
		If(waveexists(zz_image_ff_histo)!=1)
			abort "Need to run HYBRID once"
		endif
		If(ghy_range_z<0||ghy_nncon_z<2)
			abort "Need to specify histogram range and bins in the Result plotting control section"
		endif
		mirrorlength = dimdelta(wmirror_lz,0)*(dimsize(wmirror_lz,0)-1)
		mirror_npts = round(dimsize(wmirror_lz,0)/2)*2
		nncon = dimsize(zz_image_ff_histo,0)
		halfrange_ff = (dimsize(zz_image_ff_histo,0)-1)*dimdelta(zz_image_ff_histo,0)/2
		halfrange_nf = (dimsize(zz_image_nf_histo,0)-1)*dimdelta(zz_image_nf_histo,0)/2
		wave wmirror_lz
		Duplicate/O wmirror_lz wmirror_lz_backup	
	endif

	//create new surface profile
	If(newse==2)
		variable freq_min = 1
		variable freq_max = 100
		Variable RandomSeed	=0.1
		Variable slo1 = -3.0
		prompt slo1, "log(PSD) vs log(f) slope, default:-3" 
		Prompt mirrorlength, "Mirror length ("+StringFromList(ghy_lengthunit-1, "cm;mm")+")"
		Prompt mirror_npts, "Number of points"
		Prompt freq_min, "Lowest frequency (>=1)"
		Prompt freq_max, "Highest frequency"
		Prompt RandomSeed, "Random seed between 0 and 1"
		doPrompt "Create mirror in y, flat in x", slo1, mirrorlength, mirror_npts, freq_min, freq_max, RandomSeed
		if (V_Flag)
			return -1								// User canceled
		endif
		//hy_CreateSurfaceFile_range("mirror_tmp",mirror_npts,mirrorlength/mirror_npts,freq_min,freq_max,randomseed)
		hy_CreateSurfaceFile_range_new("mirror_tmp","he",1e-6,slo1,mirror_npts,mirrorlength/mirror_npts,freq_min,freq_max,randomseed)
		wave mirror_tmp
		If(ghy_diff_plane == 1)
			Duplicate/O mirror_tmp wmirror_lx
		elseif(ghy_diff_plane == 2)
			Duplicate/O mirror_tmp wmirror_lz
		endif
	endif
	
	//Shift mirror height to center at zero.
	If(ghy_diff_plane == 1)
		If(waveexists(wmirror_lx)!=1)
			abort "mirror profile not found"
		endif
		wavestats/z/q wmirror_lx
		wmirror_lx-=(v_max+v_min)/2
	elseif(ghy_diff_plane == 2)
		If(waveexists(wmirror_lz)!=1)
			abort "mirror profile not found"
		endif
		wavestats/z/q wmirror_lz
		wmirror_lz-=(v_max+v_min)/2
	endif

	//start slope error loop
	variable hy_nf = ghy_nf
	switch(ffornf)	
		case 1:	//far-field only
			ghy_nf = 0
			break		
		case 2:	//near-field only
			ghy_nf_only=1
			break
		case 3:	//both far-field and near-field
			ghy_nf = 1
			break
	endswitch
	If(ffornf==1 || ffornf==3)	
		make/O/N=(nn) sig_ff, centersig_ff, peak_ff, peakint_ff,fwhm_ff
		setscale/P x, slope_min, slope_del,"",sig_ff,centersig_ff, peak_ff, peakint_ff,fwhm_ff
		make/O/N=(nncon,nn) slopeall_ff
		setscale/P y, slope_min, slope_del,"",slopeall_ff
		setscale/I x, -halfrange_ff, halfrange_ff,"",slopeall_ff
	endif
	If(ffornf==2 || ffornf==3)
		make/O/N=(nn) sig_nf, centersig_nf, peak_nf, peakint_nf,fwhm_nf
		setscale/P x, slope_min, slope_del,"",sig_nf, centersig_nf, peak_nf, peakint_nf,fwhm_nf
		make/O/N=(nncon,nn) slopeall_nf
		setscale/P y, slope_min, slope_del,"",slopeall_nf
		setscale/I x, -halfrange_nf, halfrange_nf,"",slopeall_nf	
	endif
	// progress window
	NewPanel /N=ProgressPanel /W=(285,611,739,693)
	ValDisplay valdisp0,pos={18,32},size={342,18},limits={0,100,0},barmisc={0,0}
	ValDisplay valdisp0,value= _NUM:0
	ValDisplay valdisp0,mode= 3	// bar with no fractional part
	ValDisplay valdisp0,highColor=(0,65535,0)
	Button bStop,pos={375,32},size={50,20},title="Stop"
	DoUpdate /W=ProgressPanel /E=1	// mark this as our progress window	
	variable i,rmsslope,se_tmp,peakleft,peakright,halfcentralpeak
	If(ghy_diff_plane == 1)
		If (error_type==1)
				rmsslope = hy_findrmsslopefromheight("wmirror_lx",0)
		elseif (error_type==2)
				rmsslope = hy_findrmserror("wmirror_lx",0)
		endif
		duplicate/O wmirror_lx wmirror_lx_tmp
	endif
	If(ghy_diff_plane == 2)
		If (error_type==1)
				rmsslope = hy_findrmsslopefromheight("wmirror_lz",0)
		elseif (error_type==2)
				rmsslope = hy_findrmserror("wmirror_lz",0)
		endif
		duplicate/O wmirror_lz, wmirror_lz_tmp
	endif			
	For(i=0;i<nn;i+=1)
		//horizontal slope to p-v
		If(error_type==1)
			se_tmp = (i*slope_del+slope_min)*1e-6
		elseif (error_type==2)
			If (ghy_lengthunit==1)
				se_tmp = (i*slope_del+slope_min)*1e-7
			elseif (ghy_lengthunit==2)
				se_tmp = (i*slope_del+slope_min)*1e-6
			endif
		endif
		If(ghy_diff_plane == 1)
			wmirror_lx=wmirror_lx_tmp*se_tmp/rmsslope
		elseif(ghy_diff_plane == 2)
			wmirror_lz=wmirror_lz_tmp*se_tmp/rmsslope
		endif
		hy_prop()
		hy_conv()
		If(ghy_diff_plane == 1)
			If(ffornf==1 || ffornf==3)	
					sig_ff[i]= hy_GetStanDev("xx_image_ff_histo",-inf,inf)
					fwhm_ff[i] = sh_FindFWHM("xx_image_ff_histo")
					wavestats/q xx_image_ff_histo
					peak_ff[i] = v_max
					peakleft = dimoffset(xx_image_ff_histo,0)+dimdelta(xx_image_ff_histo,0)*v_maxRowloc-fwhm_ff[0]
					peakright = dimoffset(xx_image_ff_histo,0)+dimdelta(xx_image_ff_histo,0)*v_maxRowloc+fwhm_ff[0]
					peakint_ff[i] =  sum(xx_image_ff_histo,peakleft,peakright)/sum(ref_screen)
					centersig_ff[i] = hy_GetStanDev("xx_image_ff_histo",-2*fwhm_ff[0],2*fwhm_ff[0])	
					slopeall_ff[][i]=xx_image_ff_histo(x)
			endif
			if(ffornf==2 || ffornf==3)
					sig_nf[i]= hy_GetStanDev("xx_image_nf_histo",-inf,inf)
					fwhm_nf[i] = sh_FindFWHM("xx_image_nf_histo")
					wavestats/q xx_image_nf_histo
					peak_nf[i] = v_max
					peakleft = dimoffset(xx_image_nf_histo,0)+dimdelta(xx_image_nf_histo,0)*v_maxRowloc-fwhm_nf[0]
					peakright = dimoffset(xx_image_nf_histo,0)+dimdelta(xx_image_nf_histo,0)*v_maxRowloc+fwhm_nf[0]
					peakint_nf[i] =  sum(xx_image_nf_histo,peakleft,peakright)/sum(ref_screen)
					centersig_nf[i]= hy_GetStanDev("xx_image_nf_histo",-2*fwhm_nf[0],2*fwhm_nf[0])	
					slopeall_nf[][i]=xx_image_nf_histo(x)
			endif	
		elseif(ghy_diff_plane == 2)
			If(ffornf==1 || ffornf==3)	
					sig_ff[i]= hy_GetStanDev("zz_image_ff_histo",-inf,inf)
					fwhm_ff[i] = sh_FindFWHM("zz_image_ff_histo")
					wavestats/q zz_image_ff_histo
					peak_ff[i] = v_max
					peakleft = dimoffset(zz_image_ff_histo,0)+dimdelta(zz_image_ff_histo,0)*v_maxRowloc-fwhm_ff[0]
					peakright = dimoffset(zz_image_ff_histo,0)+dimdelta(zz_image_ff_histo,0)*v_maxRowloc+fwhm_ff[0]
					peakint_ff[i] =  sum(zz_image_ff_histo,peakleft,peakright)/sum(ref_screen)
					centersig_ff[i] = hy_GetStanDev("zz_image_ff_histo",-2*fwhm_ff[0],2*fwhm_ff[0])	
					slopeall_ff[][i]=zz_image_ff_histo(x)
			endif
			If(ffornf==2 || ffornf==3)
					sig_nf[i]= hy_GetStanDev("zz_image_nf_histo",-inf,inf)
					fwhm_nf[i] = sh_FindFWHM("zz_image_nf_histo")
					wavestats/q zz_image_nf_histo
					peak_nf[i] = v_max
					peakleft = dimoffset(zz_image_nf_histo,0)+dimdelta(zz_image_nf_histo,0)*v_maxRowloc-fwhm_nf[0]
					peakright = dimoffset(zz_image_nf_histo,0)+dimdelta(zz_image_nf_histo,0)*v_maxRowloc+fwhm_nf[0]
					peakint_nf[i] =  sum(zz_image_nf_histo,peakleft,peakright)/sum(ref_screen)
					centersig_nf[i]= hy_GetStanDev("zz_image_nf_histo",-2*fwhm_nf[0],2*fwhm_nf[0])		
					slopeall_nf[][i]=zz_image_nf_histo(x)
			endif				
		endif
		ValDisplay valdisp0,value= _NUM:i*100/nn,win=ProgressPanel
		DoUpdate /W=ProgressPanel
		if( V_Flag == 2 )	// we only have one button and that means stop
			If(ghy_diff_plane == 1)
				Duplicate/O wmirror_lx_backup wmirror_lx
			elseif(ghy_diff_plane == 2)
				Duplicate/O wmirror_lz_backup wmirror_lz	
			endif	
			ghy_nf = hy_nf
			ghy_nf_only=0
			break
		endif
	endfor
	Killwindow ProgressPanel
	If(plotornot==1&&(ffornf==1 || ffornf==3))	
		NewWaterfall/N=hyplot slopeall_ff
		ModifyWaterfall angle= 90
		ModifyWaterfall axlen= 0.7
		ModifyGraph tick=2,fSize=14,standoff=0,font="Times New Roman",notation(bottom)=1
		ModifyGraph margin(left)=58,margin(bottom)=43,margin(top)=14,margin(right)=58,width=216,height=360
		Label bottom "X or Z ("+StringFromList(ghy_lengthunit-1, "cm;mm")+")"
		Label left "Intensity (far-field)"
		If(error_type==1)
			Label right "Slope error (µrad)"
		else
			Label right "Height error (nm)"
		endif
	endif
	If(plotornot==1&&(ffornf==2 || ffornf==3))	
		NewWaterfall/N=hyplot slopeall_nf
		ModifyWaterfall angle= 90
		ModifyWaterfall axlen= 0.7
		ModifyGraph tick=2,fSize=14,standoff=0,font="Times New Roman",notation(bottom)=1
		ModifyGraph margin(left)=58,margin(bottom)=43,margin(top)=14,margin(right)=58,width=216,height=360
		Label bottom "X or Z ("+StringFromList(ghy_lengthunit-1, "cm;mm")+")"
		Label left "Intensity (near-field)"
		If(error_type==1)
			Label right "Slope error (µrad)"
		else
			Label right "Height error (nm)"
		endif
	endif
		
	//Change back to original conditions
	If(ghy_diff_plane == 1)
		Duplicate/O wmirror_lx_backup wmirror_lx
	elseif(ghy_diff_plane == 2)
		Duplicate/O wmirror_lz_backup wmirror_lz	
	endif	
	ghy_nf = hy_nf
	ghy_nf_only=0
	killwaves/z wmirror_lz_backup,wmirror_lx_backup,wmirror_lz_tmp,wmirror_lx_tmp,mirror_tmp
End

Function hy_longi(hy_input_longi) : ButtonControl
	String hy_input_longi
	NVAR/Z ghy_nf_only,ghy_distance,ghy_diff_plane,ghy_range_x,ghy_range_z,ghy_nncon_x,ghy_nncon_z,ghy_nf,ghy_lengthunit
	wave/Z xx_image_nf_histo,zz_image_nf_histo
	variable nn = 11			// number of drift points (odd number to have drift 0)
	variable longi_range = 0.2	// user unit
	Prompt longi_range, "Propagation distance ("+StringFromList(ghy_lengthunit-1, "cm;mm")+"):"
	Prompt nn, "Number of points (odd number preferred)"
	DoPrompt "Longitudinal profiles", longi_range,nn
	if (V_flag==1)
		return 0
	endif
	variable drift_delta = longi_range/(nn-1)
	If(ghy_diff_plane == 1)
		If(waveexists(xx_image_nf_histo)!=1||ghy_nf!=1)
			abort "Need to run HYBRID near-field once"
		endif
		If(ghy_range_x<0||ghy_nncon_x<2)
			abort "Need to specify histogram range and bins in the Result plotting control section"
		endif
		make/O/N=(nn,dimsize(xx_image_nf_histo,0)) longiall
		setscale/I x, -longi_range/2, longi_range/2,"",longiall
		setscale/P y, dimoffset(xx_image_nf_histo,0), dimdelta(xx_image_nf_histo,0),"",longiall		
	elseif(ghy_diff_plane == 2)
		If(waveexists(zz_image_nf_histo)!=1||ghy_nf!=1)
			abort "Need to run HYBRID near-field once"
		endif
		If(ghy_range_z<0||ghy_nncon_z<2)
			abort "Need to specify histogram range and bins in the Result plotting control section"
		endif
		make/O/N=(nn,dimsize(zz_image_nf_histo,0)) longiall
		setscale/I x, -longi_range/2, longi_range/2,"",longiall
		setscale/P y, dimoffset(zz_image_nf_histo,0), dimdelta(zz_image_nf_histo,0),"",longiall		
	endif
	make/O/N=(nn) sig_longi,fwhm_longi
	setscale/I x, -longi_range/2, longi_range/2,"",sig_longi,fwhm_longi

	//start longitudinal loop
	ghy_nf_only = 1	//to tell hy_prop() it is near-field only
	variable hy_distance = ghy_distance
	variable i
	NewPanel /N=ProgressPanel /W=(285,611,739,693)
	ValDisplay valdisp0,pos={18,32},size={342,18},limits={0,100,0},barmisc={0,0}
	ValDisplay valdisp0,value= _NUM:0
	ValDisplay valdisp0,mode= 3	// bar with no fractional part
	ValDisplay valdisp0,highColor=(0,65535,0)
	Button bStop,pos={375,32},size={50,20},title="Stop"
	DoUpdate /W=ProgressPanel /E=1	// mark this as our progress window
	For(i=0;i<nn;i+=1)
		ghy_distance = hy_distance+(i-(nn-1)/2)*drift_delta
		hy_prop()
		hy_conv()
		If(ghy_diff_plane == 1)
			longiall[i][]=xx_image_nf_histo(y)
			fwhm_longi[i] = sh_findfwhm("xx_image_nf_histo")
			CurveFit/Q/M=2/W=2 gauss, xx_image_nf_histo/D
			wave w_coef
			sig_longi[i] = w_coef[3]/sqrt(2)	//hy_GetStanDev("xx_image_nf_histo",-inf,inf)
		elseif(ghy_diff_plane == 2)
			longiall[i][]=zz_image_nf_histo(y)
			fwhm_longi[i] = sh_findfwhm("zz_image_nf_histo")
			CurveFit/Q/M=2/W=2 gauss, zz_image_nf_histo/D
			wave w_coef
			sig_longi[i] = w_coef[3]/sqrt(2)	//hy_GetStanDev("zz_image_nf_histo",-inf,inf)
		endif
		ValDisplay valdisp0,value= _NUM:i*100/nn,win=ProgressPanel
		DoUpdate /W=ProgressPanel
		if( V_Flag == 2 )	// we only have one button and that means stop
			ghy_nf_only = 0
			ghy_distance = hy_distance
			break
		endif		
	endfor
	killwaves/z fit_zz_image_nf_histo,fit_xx_image_nf_histo
	Killwindow ProgressPanel
	Display/N=hyplot;AppendImage longiall
	ModifyImage longiall ctab= {*,*,Geo,1}
	ModifyGraph tick=2,fSize=14,standoff=0,notation=1,font="Times New Roman"
	ModifyGraph width=288,height=216,margin(left)=50,margin(bottom)=43,margin(top)=14,margin(right)=14
	Label left "X or Z ("+StringFromList(ghy_lengthunit-1, "cm;mm")+")";DelayUpdate
	Label bottom "Longitudinal position ("+StringFromList(ghy_lengthunit-1, "cm;mm")+")"
	Display/N=hyplot sig_longi
	ModifyGraph tick=2,fSize=14,standoff=0,notation=1,font="Times New Roman",mirror=2
	ModifyGraph width=288,height=216,margin(left)=50,margin(bottom)=43,margin(top)=14,margin(right)=14
	Label left "rms size ("+StringFromList(ghy_lengthunit-1, "cm;mm")+")";DelayUpdate
	Label bottom "Longitudinal position ("+StringFromList(ghy_lengthunit-1, "cm;mm")+")"
	Display/N=hyplot fwhm_longi
	ModifyGraph tick=2,fSize=14,standoff=0,notation=1,font="Times New Roman",mirror=2
	ModifyGraph width=288,height=216,margin(left)=50,margin(bottom)=43,margin(top)=14,margin(right)=14
	Label left "FWHM size ("+StringFromList(ghy_lengthunit-1, "cm;mm")+")";DelayUpdate
	Label bottom "Longitudinal position ("+StringFromList(ghy_lengthunit-1, "cm;mm")+")"
	//turn near-field only off
	ghy_nf_only = 0
	ghy_distance = hy_distance
End

Function hy_cleanup(hy_input_cleanup) : ButtonControl
	String hy_input_cleanup
	Killwaves/z shstar,xx_star,zz_star,shscreen,wenergy,dz_conv,dx_conv
	Killwaves/z zz_image_ff,zz_image_ff_histo,zz_wave,zz_image_nf,zz_image_nf_histo
	Killwaves/z xx_image_ff,xx_image_ff_histo,xx_wave,xx_image_nf,xx_image_nf_histo
	Killwaves/z xx_image_ffzz_image_ff,xx_image_ffzz_image_ffx,xx_image_ffzz_image_ffz
	Killwaves/z wmirror,angle_inc,xx_screen,zz_screen,ref_screen,xx_mirr,yy_mirr,wwavelength,dx_ray,dz_ray
	Killwaves/z wmirror,wmirror_lx,wmirror_lz,wangle_z,wangle_x,wlz,wlx,wIray_2d,wIray_x,wIray_z,wangle_ref_x,wangle_ref_z
	Killwaves/z xx_screen,zz_screen,xp_screen,yp_screen,zp_screen,ref_screen,xx_focal_ray, zz_focal_ray
	Killwaves/z dif_xp,dif_x,dif_zp,dif_z,dif_xz,dif_xpzp,dx_ray,dz_ray
End

//read shadow gfile in to a long string list gfile. need to use NumberByKey(parametername,gfile) to access the number.
Function/S sh_read_gfile(gfilename)
	string gfilename
	Variable refnum
	If (strlen(gfilename) == 0)
		open/M="Read Shadow start file"/R/T="????" refnum
	else
		open/M="Read Shadow start file"/R/T="????" refnum as gfilename
	Endif
	FStatus refnum								// get the file status 
	If (V_flag == 0)								// When cancel was clicked, V_flag=1				
		Abort 									// Abort
	Endif
	Variable lineNumber, len
	String buffer,gfile
	gfile=""
	do
		FReadLine refNum, buffer
		len = strlen(buffer)
		if (len == 0)
			break						// No more lines to be read
		endif
		gfile+= buffer[0,strsearch(buffer,"=",0)-2]+":"+buffer[strsearch(buffer,"=",0)+2,len-1]+";"
	while (1)
	print "Shadow gfile readed", gfilename
	return gfile	
End

Function/S sh_readsh(shfilename,flag,shname)	
	string shfilename,shname
	variable flag	//flag = 0: all rays, 1: good rays, 2:lost rays
	Variable refnum
	if(strlen(shname)==0)
	    shname="shdata"
	 endif
	If (strlen(shfilename) == 0)
		open/M="Load Shadow Binary file"/R/T="????" refnum
		print "Shadow file loaded: ", S_filename 
	else
		If(stringmatch(":",shfilename[strlen(shfilename)-1]) == 1)
			NewPath/O/Q tmppath, shfilename
			open/M="Load Shadow Binary file"/R/P=tmppath/T="????" refnum
			print "Shadow file loaded: ", S_filename 
			KillPath/Z tmppath		
		else
			open/M="Load Shadow Binary file"/R/T="????" refnum as shfilename
			print "Shadow file loaded: ", shfileName
		endif
	Endif
	FStatus refnum								// get the file status 
	If (V_flag == 0)								// When cancel was clicked, V_flag=1				
		Abort 									// Abort
	Endif
	Make/O/N=5/I header						// 20 byte header: 4+4+4+4+4					
	FbinRead/B=0/F=0 refnum, header
	Variable Ncol = header[1]						// number of columns
	Variable Npoint = header[2]						// number of rays
	// Each line is 152 (4+8*18+4) bytes for 18 column, 112 (4+8*13+4) bytes for 13 column
	If (Ncol == 18)
		  Make/O/N=(19,Npoint)/D  $shname 
		  Make/o/n=(19,Npoint-1)/D   datastorage
		  Make/o/n=(18,1)/D    lastray
	Else
		  Make/O/N=(14,Npoint)/D  $shname 
		  make/o/n=(14,Npoint-1)/D   datastorage
		  make/o/n=(13,1)/D lastray
	Endif
	wave shdata=$shname
	
	
	// 18 columns
	
	Variable i=0
	FStatus refnum
	Make/O/N=1/I terminator
	FBinRead/B=0/F=0 refnum, terminator
	FBinRead/B=0/F=0 refnum, datastorage
	FBinRead/B=0/F=0 refnum, lastray
       FBinRead/B=0/F=0 refnum, terminator
	Close refnum
	shdata[][]=datastorage[p][q]
	shdata[][Npoint-1]=lastray[p][q]
	
	print "Total number of rays", dimsize(shdata,1)
//	shdata[10][]*=1.239852e-4/6.283185307179586476925287		// convert the energy unit to eV
	
	If(flag>0)
		Make/O/D/N=(Npoint) F_lost				// Lost ray flag
		F_lost=shdata[9][p]
		wavestats/q/z F_lost
		If((v_min!=1)||(v_max!=1))
			Make/O/D/N=(Npoint) Index, tmp			// Ray index
			If(flag == 1)
				makeindex/R F_lost, index
			else
				makeindex F_lost, index
			endif
			Indexsort index, F_lost
			for(i=0;i<dimsize(shdata,0)-1;i+=1)
				tmp = shdata[i][p]
				Indexsort index, tmp
				shdata[i][] = tmp[q]
			endfor
			wavestats/q/z F_lost
			If(flag == 1)
				If ((v_min!=v_max)&&(v_min<=0))
					do
						DeletePoints/M=1  v_minloc, Npoint-v_minloc, shdata
						deletepoints v_minloc, Npoint-v_minloc, F_lost
						Npoint=v_minloc
						wavestats/q/z F_lost
					while(v_min!=v_max)
				Endif
			else
				If (v_max==1)
					DeletePoints/M=1  V_maxloc, Npoint-V_maxloc, shdata
					deletepoints V_maxloc, Npoint-V_maxloc, F_lost
					Npoint=V_maxloc
				Endif			
			endif			
		else
			if (flag==2)
				killwaves/z shdata
				npoint = 0
				Doalert 0, "No lost rays"
			endif
		endif
	endif
	print "Number of good rays", dimsize(shdata,1)
	killwaves/z F_lost,index,tmp, header, terminator, datastorage, lastray
	return shname
End

Function sh_putrays(shfilename,shdata)
	wave shdata
	string shfilename
//	shdata[10][]/=1.239852e-4/6.283185307179586476925287		// convert the energy unit from eV to shadow unit
	Make/O/N=5/I header						
	header[0]=12	
	header[1] = dimsize(shdata,0)-1
	header[2] = dimsize(shdata,1)
	header[3]=0
	header[4]=12
	Make/O/N=1/I  terminator=header[1]*8
	If (header[1] == 18)
		  Make/o/n=(19,header[2]-1)/D   datastorage
		  Make/o/n=(18,1)/D    lastray
	Else	
		  make/o/n=(14,header[2]-1)/D   datastorage
		  make/o/n=(13,1)/D lastray
	Endif
       datastorage[][]=shdata[p][q]
	lastray[][]=shdata[p][header[2]-1]
	Variable refnum	
	If (strlen(shfilename) == 0)
		open/M="Save Shadow Binary file"/T="BINA" refnum
	else
		If(stringmatch(":",shfilename[strlen(shfilename)-1]) == 1)
			NewPath/O/Q tmppath, shfilename
			open/M="Save Shadow Binary file"/P=tmppath/T="BINA" refnum		
			KillPath/Z tmppath		
		else
			open/M="Save Shadow Binary file"/T="BINA" refnum as shfilename
		endif
	Endif
	FbinWrite/B=0/F=0 refnum, header		
	FbinWrite/B=0/F=0 refnum,terminator
	FbinWrite/B=0/F=0 refnum, datastorage
	FbinWrite/B=0/F=0 refnum, lastray
	FbinWrite/B=0/F=0 refnum,terminator
	FStatus refnum								
	If (V_flag == 0)										
		Abort 								
	Endif
	close refnum
	killwaves/z header,datastorage,lastray,terminator
	print "Shadow binary file saved as:  ", shfilename
//	shdata[10][]*=1.239852e-4/6.283185307179586476925287		// convert the energy unit to eV
End

Function/S sh_getshcol(shdata,col, flag,colname)	
	wave shdata
	variable col,flag //flag = 0: all rays, 1: good rays, 2:lost rays
	string colname
	//           1   X spatial coordinate [user's unit]
	//           2   Y spatial coordinate [user's unit]
	//           3   Z spatial coordinate [user's unit]
	//           4   Xp direction or divergence [rads]
	//           5   Yp direction or divergence [rads]
	//           6   Zp direction or divergence [rads]
	//           7   X component of the electromagnetic vector (s-polariz)
	//           8   Y component of the electromagnetic vector (s-polariz)
	//           9   Z component of the electromagnetic vector (s-polariz)
	//          10   Lost ray flag
	//          11   Energy [eV]
	//          12   Ray index
	//          13   Optical path length
	//          14   Phase (s-polarization)
	//          15   Phase (p-polarization)
	//          16   X component of the electromagnetic vector (p-polariz)
	//          17   Y component of the electromagnetic vector (p-polariz)
	//          18   Z component of the electromagnetic vector (p-polariz)
	//          19   Wavelength [A]
	//          20   R= SQRT(X^2+Y^2+Z^2)
	//          21   angle from Y axis
	//          22   the magnitude of the Electromagnetic vector
	//          23   |E|^2 (total intensity)
	//          24   total intensity for s-polarization
	//          25   total intensity for p-polarization
	//          26   K=2 pi/lambda [A^-1]
	//          27   Kx = K * col4 [A^-1]
	//          28   Ky = K * col5 [A^-1]
	//          29   Kx = K * col6 [A^-1]
	//          30   S0-stokes = |Es|^2 + |Ep|^2
	//          31   S1-stokes = |Es|^2 - |Ep|^2
	//          32   S2-stokes = 2 |Es| |Ep| cos(phase_s-phase_p)
	//          33   S3-stokes = 2 |Es| |Ep| sin(phase_s-phase_p)
	//          34   CohS      = |Es| sin(phase_s)
	//          35   CohP      = |Ep| sin(phase_p)
	//          36   |Es| cos(phase_s)
	//          37   |Ep| cos(phase_p)

	shdata[10][]*=1.239852e-4/6.283185307179586476925287	//	Energy convert to eV	
	If(strlen(colname)==0)
		colname = "col"+num2str(col)
	endif
	variable npoint = dimsize(shdata,1)
	make/N=(npoint)/O/D $colname
	wave output=$colname

	If(col<dimsize(shdata,0))
		output = shdata[col-1][p]
	else
		switch(col)												
			case 19:
				output = 12398.4172/(shdata[10][p])		//	19   Wavelength [A]
				break
			case 20:
				output = sqrt(shdata[0][p]^2+shdata[1][p]^2+shdata[2][p]^2)	//	20   R= SQRT(X^2+Y^2+Z^2)
				break
			case 21:
				output = acos(shdata[4][p])	//	 21   angle from Y axis
				break
			case 22:
				output = shdata[6][p]^2+shdata[7][p]^2+shdata[8][p]^2
				If(dimsize(shdata,0)==19)
					output += shdata[15][p]^2+shdata[16][p]^2+shdata[17][p]^2
				endif
				output = sqrt(output)  	//	22   the magnitude of the Electromagnetic vector
				break
			case 23:
				output = shdata[6][p]^2+shdata[7][p]^2+shdata[8][p]^2
				If(dimsize(shdata,0)==19)
					output += shdata[15][p]^2+shdata[16][p]^2+shdata[17][p]^2
				endif		//	23   |E|^2 (total intensity)
				break
			case 24:
				output = shdata[6][p]^2+shdata[7][p]^2+shdata[8][p]^2	//	24   total intensity for s-polarization
				break
			case 25:
				If(dimsize(shdata,0)==19)
					output = shdata[15][p]^2+shdata[16][p]^2+shdata[17][p]^2		//	25   total intensity for p-polarization
				else
					output = 0
				endif
				break
			case 26:
				output = 2*pi/(12398.4172/shdata[10][p])	//	26   K=2 pi/lambda [A^-1]
				break
			case 27:
				output = 2*pi/(12398.4172/shdata[10][p])*shdata[3][p]	//	27   Kx = K * col4 [A^-1]
				break
			case 28:
				output = 2*pi/(12398.4172/shdata[10][p])*shdata[4][p]	//	28   Ky = K * col5 [A^-1]
				break
			case 29:
				output = 2*pi/(12398.4172/shdata[10][p])*shdata[5][p]	//	29   Kz = K * col6 [A^-1]
				break
			case 30:
				output = shdata[6][p]^2+shdata[7][p]^2+shdata[8][p]^2
				If(dimsize(shdata,0)==19)
					output += shdata[15][p]^2+shdata[16][p]^2+shdata[17][p]^2
				endif		//	30   S0-stokes = |Es|^2 + |Ep|^2
				break
			case 31:
				output = shdata[6][p]^2+shdata[7][p]^2+shdata[8][p]^2
				If(dimsize(shdata,0)==19)
					output -= shdata[15][p]^2+shdata[16][p]^2+shdata[17][p]^2
				endif	//	31   S1-stokes = |Es|^2 - |Ep|^2
				break
			case 32:
				If(dimsize(shdata,0)==19)
					sh_getphase(shdata)
					wave shphase
					output = 2*sqrt(shdata[6][p]^2+shdata[7][p]^2+shdata[8][p]^2)*sqrt(shdata[15][p]^2+shdata[16][p]^2+shdata[17][p]^2)*cos(shphase[0][p]-shphase[1][p])
					killwaves/z shphase
				else
					output = 0
				endif	//	32   S2-stokes = 2 |Es| |Ep| cos(phase_s-phase_p)
				break
			case 33:
				If(dimsize(shdata,0)==19)
					sh_getphase(shdata)
					wave shphase
					output = 2*sqrt(shdata[6][p]^2+shdata[7][p]^2+shdata[8][p]^2)*sqrt(shdata[15][p]^2+shdata[16][p]^2+shdata[17][p]^2)*sin(shphase[0][p]-shphase[1][p])
					killwaves/z shphase
				else
					output = 0
				endif	//	33   S3-stokes = 2 |Es| |Ep| sin(phase_s-phase_p)
				break
			case 34:
				sh_getphase(shdata)
				wave shphase
				output = sqrt(shdata[6][p]^2+shdata[7][p]^2+shdata[8][p]^2)*sin(shphase[0][p])	//	34   CohS      = |Es| sin(phase_s)
				killwaves/z shphase
				break
			case 35:
				If(dimsize(shdata,0)==19)
					sh_getphase(shdata)
					wave shphase
					output =sqrt(shdata[15][p]^2+shdata[16][p]^2+shdata[17][p]^2)*sin(shphase[1][p])
					killwaves/z shphase
				else
					output = 0
				endif	//	35   CohP      = |Ep| sin(phase_p)
				break
			case 36:
				sh_getphase(shdata)
				wave shphase
				output = sqrt(shdata[6][p]^2+shdata[7][p]^2+shdata[8][p]^2)*cos(shphase[0][p])	//          34   CohS      = |Es| sin(phase_s)
				killwaves/z shphase	//	36   |Es| cos(phase_s)

				break
			case 37:
				If(dimsize(shdata,0)==19)
					sh_getphase(shdata)
					wave shphase
					output =sqrt(shdata[15][p]^2+shdata[16][p]^2+shdata[17][p]^2)*cos(shphase[1][p])
					killwaves/z shphase
				else
					output = 0
				endif		//	37   |Ep| cos(phase_p)
				break
			default:
				output = 0
				break
		endswitch
	endif
	If(flag>0)
		Make/O/D/N=(npoint) F_lost				// Lost ray flag
		F_lost=shdata[9][p]
		wavestats/q/z F_lost
		If((v_min!=1)||(v_max!=1))
			If(flag == 1)
				sort/R F_lost, F_lost, output
				wavestats/q/z F_lost
				If ((v_min!=v_max)&&(v_min<=0))
					do
						deletepoints v_minloc, Npoint-v_minloc, F_lost, output
						Npoint=v_minloc
						wavestats/q/z F_lost
					while(v_min!=v_max)
				Endif
			else
				sort F_lost, F_lost, output
				wavestats/q/z F_lost
				If (v_max==1)
					deletepoints V_maxloc, Npoint-V_maxloc, F_lost, output
					Npoint=V_maxloc
				Endif	
			endif
		else
			if (flag==2)
				killwaves/z output
				npoint = 0
				Doalert 0, "No lost rays"
			endif
		endif
	endif
	killwaves/z F_lost
	shdata[10][]/=1.239852e-4/6.283185307179586476925287
	return colname
End

Function sh_getphase(shdata)
	wave shdata
	make/N=(4,dimsize(shdata,1))/D/O shphase
	sh_getshcol(shdata,14, 0,"phase_s")
	sh_getshcol(shdata,15, 0,"phase_p")
	sh_getshcol(shdata,7, 0,"e_s")
	sh_getshcol(shdata,18, 0,"e_p")
	wave phase_s,phase_p,e_s,e_p
	shphase[2][] = phase_s[q]
	shphase[3][] = phase_p[q]
	variable i
	For(i=0;i<dimsize(phase_s,0);i+=1)
		if (e_s[i]<0)
			phase_s[i] += pi
		endif
		if (e_p[i]<0)
			phase_p[i] += pi
		endif
	endfor
	shphase[0][] = phase_s[q]
	shphase[1][] = phase_p[q]
	killwaves/z phase_s,phase_p,e_s,e_p
End


		
Function sh_readangle(filename,flag)
	String filename
	variable flag
	If (strlen(filename) == 0)
		LoadWave/Q/G/O/D/L={0,0,5000000,0,4}/N=angletemp
		print "Angle file loaded: ", S_path,S_filename 
	else
		If(stringmatch(":",filename[strlen(filename)-1]) == 1)
			NewPath/O/Q tmppath, filename
			LoadWave/Q/P=tmppath/G/O/D/L={0,0,5000000,0,4}/N=angletemp
			print "Angle file loaded: ", S_path,S_filename 
			KillPath/Z tmppath		
		else
			LoadWave/Q/G/O/D/L={0,0,5000000,0,4}/N=angletemp filename
			print "Angle file loaded: ", filename 
		endif
	Endif
	Wave angletemp0, angletemp1, angletemp2, angletemp3
	Duplicate/O angletemp0 angle_index
	Duplicate/O angletemp1 angle_inc
	Duplicate/O angletemp2 angle_ref
	Duplicate/O angletemp3 angle_flag
	killwaves/z angletemp0, angletemp1, angletemp2, angletemp3
	variable npoint = dimsize(angle_flag,0)
	If(flag>0)
		wavestats/q/z angle_flag
		If((v_min!=1)||(v_max!=1))
			If(flag == 1)
				sort/R angle_flag, angle_flag, angle_index, angle_inc, angle_ref
				wavestats/q/z angle_flag
				If ((v_min!=v_max)&&(v_min<=0))
					do
						deletepoints v_minloc, Npoint-v_minloc, angle_flag, angle_index, angle_inc, angle_ref
						Npoint=v_minloc
						wavestats/q/z angle_flag
					while(v_min!=v_max)
				Endif
			else
				sort angle_flag, angle_flag, angle_index, angle_inc, angle_ref
				wavestats/q/z angle_flag
				If (v_max==1)
					deletepoints V_maxloc, Npoint-V_maxloc, angle_flag, angle_index, angle_inc, angle_ref
					Npoint=V_maxloc
				Endif	
			endif
		else
			if (flag==2)
				killwaves/z angle_flag, angle_index, angle_inc, angle_ref
				npoint = 0
				Doalert 0, "No lost rays"
			endif
		endif
	endif
End

Function sh_readsurface(filename,outputname)
	String filename,outputname
	If (strlen(filename) == 0)
		Loadwave/Q/J/N=tmp/L={0,0,0,0,0}/M
		filename = S_path+S_fileName
	Endif
	killwaves/z tmp0
	Loadwave/Q/J/N=tmp/L={0,0,1,0,2}/M filename
	print "mirror surface loaded from file:", filename
	wave tmp0
	Variable nx = tmp0[0][0]
	Variable ny = tmp0[0][1]
	make/N=(ny)/O/D yvalues
	make/N=(nx)/O/D xvalues
	make/N=(nx,ny)/O/D $outputname
	wave surface = $outputname
	Loadwave/D/Q/J/N=tmp/V={"\t "," $",0,1}/L={0,1,1,0,ny}/M filename
	yvalues = tmp0[0][p]
	variable i=-1
	variable blank=-1
	Do
		i+=1
		blank+=1		
	while(numtype(yvalues[i])==2)
	If(blank>0)
		Loadwave/D/Q/J/N=tmp/V={"\t "," $",0,1}/L={0,1,1,blank,ny}/M filename
		yvalues = tmp0[0][p]
	endif	
	Loadwave/D/Q/J/N=tmp/V={"\t "," $",0,1}/L={0,2,nx,blank,ny+1}/M filename
	xvalues = tmp0[p][0]
	surface[][]=tmp0[p][q+1]
	setscale/I x, xvalues[0], xvalues[nx-1], "", surface
	setscale/I y, yvalues[0], yvalues[ny-1], "", surface
	killwaves/z tmp0, xvalues, yvalues
end

Function sh_readsurface_mac(filename,outputname)
	String filename,outputname
	If (strlen(filename) == 0)
		Loadwave/Q/J/N=tmp/L={0,0,0,0,0}/M
		filename = S_path+S_fileName
	Endif
	print filename
	Loadwave/O/Q/F={2,12,0}/N=tmp/L={0,0,1,0,2}/M filename
	wave tmp0
	Variable nx = tmp0[0][0]
	Variable ny = tmp0[0][1]
	Variable nrows = 1+ceil(ny/5)+ny*nx
	Variable ncols = min(5,ny)
	Loadwave/O/D/Q/F={ncols,16,0}/N=tmp/L={0,0,nrows,0,ncols}/M filename	
	make/N=(ny)/O/D yvalues
	make/N=(nx)/O/D xvalues
	make/N=(nx,ny)/O/D $outputname
	wave zvalues = $outputname
	Variable i, j
	For(i=0;i<ny;i+=1)
		yvalues[i] = tmp0[1+floor(i/ncols)][mod(i,ncols)]
	Endfor
	For(i=0;i<nx;i+=1)
		xvalues[i] = tmp0[1+ceil(ny/ncols)+i*ny][0]
		zvalues[i][] =  tmp0[1+ceil(ny/ncols)+i*ny+q][0]
		zvalues[i][0] =  tmp0[1+ceil(ny/ncols)+i*ny][1]
	Endfor
	setscale/I x, xvalues[0], xvalues[nx-1], "", zvalues
	setscale/I y, yvalues[0], yvalues[ny-1], "", zvalues
	killwaves/z tmp0, xvalues, yvalues
end

Window sh_gui() : Graph
	String/G gsh_shadow3_path = "C:xop2.3:extensions:shadowvui:shadow3:"
	String/G gsh_path = "C:xop2.3:tmp:"
	Variable/G gsh_flag = 1
	string/G gsh_columnlist="X;Y;Z;Xp;Yp;Zp;Es_x;Es_y;Es_z;flag;Energy_eV;Index;Pathlength;Phase_s;Phase_p;Ep_x;Ep_y;Ep_z;lambda;R;AngleFromY;|E|;|E|^2;Es^2;Ep^2;k;kx;ky;kz;S0;S1;S2;S3;CohS;CohP;Es cos(phase_s);Ep cos(phase_p)"
	Variable/G gsh_column = 1
	Variable/G gsh_numofOE = 3
	Variable/G gsh_firstOE = 1
	string/G gsh_starfiletypelist="star;star_hybrid"
	Variable/G gsh_starfiletype = 1
	PauseUpdate; Silent 1
	Display/k=1 /W=(360,50,470,450)
	Modifygraph gbRGB=(42662,65535,42662)
	TitleBox sh_input_textbox1,title="Shadow working directory",pos={10,10},frame=0,fsize=14
	SetVariable sh_input_path,live=1,pos={10,35},size={0,0},bodyWidth=150,fsize=14,title="  ",value=gsh_path
	TitleBox sh_input_textbox2,title="Shadow3 directory",pos={10,60},frame=0,fsize=14
	SetVariable sh_input_shadow3_path,live=1,pos={10,85},size={0,0},bodyWidth=150,fsize=14,title="  ",value=gsh_shadow3_path
	Button sh_input_runsource,pos={10,110},size={150,20},proc=sh_input_runsourcebutton,title="Run Source"	
	SetVariable sh_input_numofoe,live=1,pos={10,135},size={0,0},bodyWidth=50,fsize=14,title="    Number of OEs ",limits={1,10,1},value=gsh_numofOE
	SetVariable sh_input_firstoe,live=1,pos={10,160},size={0,0},bodyWidth=50,fsize=14,title="    First OE to trace",limits={1,10,1},value=gsh_firstOE
	PopupMenu/Z sh_input_starfiletype,live=1,pos={10,185},size={0,0},bodyWidth=72,fsize=14,title="    Star file type",mode=1,popvalue=StringFromList(gsh_starfiletype-1, gsh_starfiletypelist),value=gsh_starfiletypelist,proc=sh_updatestarfiletype
	Button sh_input_runtrace,pos={10,210},size={150,20},proc=sh_input_runtracebutton,title="Run Trace"	
	GroupBox sh_input_gb1,pos={0,238},size={190,1},frame=0		
	PopupMenu/Z sh_input_flag,live=1,pos={10,245},size={0,0},bodyWidth=100,fsize=14,title="    Read",mode=1,popvalue=StringFromList(gsh_flag, "All rays;Good only;Lost only"),value="All rays;Good only;Lost only",proc=sh_updateflag
	Button sh_input_readsh,pos={10,270},size={150,20},proc=sh_input_readshbutton,title="Read Shadow File"	
	Button sh_input_putrays,pos={10,295},size={150,20},proc=sh_input_putraysbutton,title="Write Shadow File"	
	PopupMenu/Z sh_input_column,live=1,pos={10,320},size={0,0},bodyWidth=100,fsize=14,title="    Column",mode=1,popvalue=StringFromList(gsh_column-1, gsh_columnlist),value=gsh_columnlist,proc=sh_updatecolumn
	Button sh_input_getcolumn,pos={10,345},size={150,20},proc=sh_input_getcolumnbutton,title="Get A Single Column"	
	Button sh_input_readangle,pos={10,370},size={150,20},proc=sh_input_readanglebutton,title="Read Angle File"	
	
	Button sh_input_2dhist,pos={10,395},size={150,20},proc=sh_input_2dhistbutton,title="Histogram 2d"	
	Button sh_input_1dhist,pos={10,420},size={150,20},proc=sh_input_1dhistbutton,title="Histogram 1d"	
	
	Button sh_input_closeplots,pos={10,445},size={150,20},proc=sh_input_closeplotsbutton,title="Close plots"	
	GroupBox sh_input_gb2,pos={0,473},size={190,1},frame=0
	Button sh_input_spectra_read2d,pos={10,480},size={150,20},proc=sh_input_spectra_read2dbutton,title="Read Spectra output"	
	Button sh_input_spectra_source,pos={10,505},size={150,20},proc=sh_input_spectra_sourcebutton,title="Rays from Spectra"
	Button sh_input_shifted_und,pos={10,530},size={150,20},proc=sh_input_shifted_undbutton,title="Rays for shifted undulator"	
	GroupBox sh_input_gb3,pos={0,558},size={190,1},frame=0		
//	Button readwavinessdata,pos={10,565},size={150,20},proc=readwavinessdatabutton,title="Read surface profile"
//	Button writewavinessdata,pos={10,590},size={150,20},proc=writewavinessdatabutton,title="Write 2d surface profile"
//	Button writewavinessdata1d,pos={10,615},size={150,20},proc=writewavinessdata1dbutton,title="Write 1d surface profile"

EndMacro

Function sh_updateflag(ctrlName,popNum,popStr) : PopupMenuControl
	String ctrlName
	Variable popNum	// which item is currently selected (1-based)
	String popStr		// contents of current popup item as string
	NVAR gsh_flag
	gsh_flag = popNum-1
End
Function sh_updatecolumn(ctrlName,popNum,popStr) : PopupMenuControl
	String ctrlName
	Variable popNum	// which item is currently selected (1-based)
	String popStr		// contents of current popup item as string
	NVAR gsh_column
	gsh_column = popNum
End

Function sh_updatestarfiletype(ctrlName,popNum,popStr) : PopupMenuControl
	String ctrlName
	Variable popNum	// which item is currently selected (1-based)
	String popStr		// contents of current popup item as string
	NVAR gsh_starfiletype
	gsh_starfiletype = popNum
End

Function sh_input_runsourcebutton(sh_input_runsource) : ButtonControl
	String sh_input_runsource
	SVAR gsh_path
	SVAR gsh_shadow3_path
	NewPath/O/Q shadow, gsh_path
	string inpname = gsh_path+"shadow3.inp"
	variable refnum
	open refnum as inpname
	fprintf refnum, "source"+"\r\n"
	fprintf refnum, "batch"+"\r\n"
	fprintf refnum, "start.00"+"\r\n"
	fprintf refnum, "exit"+"\r\n"
	close refnum
	sh_runshadow3()
	print "|||||||||||||||||||||||||||||||||SHADOW SOURCE|||||||||||||||||||||||||||||||||"
	print "Run shadow source and generated file: begin.dat "
End

Function sh_input_runtracebutton(sh_input_runtrace) : ButtonControl
	String sh_input_runtrace
	SVAR gsh_path
	SVAR gsh_shadow3_path
	NVAR gsh_starfiletype,gsh_numofOE,gsh_firstOE
	SVAR gsh_starfiletypelist
	string inpname = gsh_path+"shadow3.inp"
	variable refnum,i
	open refnum as inpname
	fprintf refnum, "trace"+"\r\n"
	fprintf refnum, "batch"+"\r\n"
	if(gsh_firstOE==1)
		fprintf refnum, "0"+"\r\n"
	else
		fprintf refnum, "1"+"\r\n"
		fprintf refnum, num2str(gsh_firstOE-1)+"\r\n"
		fprintf refnum, StringFromList(gsh_starfiletype-1, gsh_starfiletypelist)+"."+sh_num2index_n(gsh_firstOE-1,2)+"\r\n"
		fprintf refnum, "0"+"\r\n"
	endif
	for(i=0;i<gsh_numofOE;i+=1)
		fprintf refnum, "start."+sh_num2index_n(gsh_firstOE+i,2)+"\r\n"
		fprintf refnum, "0"+"\r\n"
	endfor
	fprintf refnum, "exit"+"\r\n"
	close refnum
	sh_runshadow3()
	print "|||||||||||||||||||||||||||||||||SHADOW TRACE||||||||||||||||||||||||||||||||||||||"
	for(i=0;i<gsh_numofOE;i+=1)
		print "Ray traced OE "+num2str(gsh_firstOE+i)+" and generated file: star."+sh_num2index_n(gsh_firstOE+i,2)
	endfor
End

function/S sh_num2index_n(index,numdigit)
	variable index,numdigit
	string sindex
	string zeros = "0000000000000000000000"
	string outstr
	variable i
	if(index>=10^(numdigit) || index<0)
		abort "index out of range"
	endif
	for(i=1;i<numdigit;i+=1)
		If(index>=10^i)
			outstr = zeros[0,numdigit-i-2]+num2istr(index)
		endif
	endfor
	if(index>=10^(numdigit-1))
		outstr = num2istr(index)
	endif
	if(index<10)
		outstr = zeros[0,numdigit-2]+num2istr(index)
	endif	
	return outstr
end

Function sh_runshadow3()
	SVAR gsh_path
	SVAR gsh_shadow3_path
	variable refnum
	string batname = gsh_path+"runshadow.bat"
	Open refnum as batname
	fprintf refnum, "cd "+sh_path_windows(gsh_path)+"\r\n"
	fprintf refnum, sh_path_windows(gsh_shadow3_path)+"shadow3.exe <shadow3.inp"+"\r\n"
	fprintf refnum, "exit"
	Close refnum
	string cmd
	cmd = "cmd.exe /k "+sh_path_windows(gsh_path)+"runshadow.bat"
	ExecuteScriptText cmd 
End

Function/S sh_path_windows(path_igor)
	string path_igor
	string path_windows
	path_windows = replacestring(":",path_igor[0,1],":\\")+path_igor[2,inf]
	path_windows = path_windows[0,2]+replacestring(":",path_windows[3,inf],"\\")
	return path_windows
End

Function sh_input_readshbutton(sh_input_readsh) : ButtonControl
	String sh_input_readsh
	NVAR gsh_flag
	SVAR gsh_path
	NewPath/O/Q shadow, gsh_path
	sh_readsh(gsh_path,gsh_flag,"")	
End

Function sh_input_putraysbutton(sh_input_putrays) : ButtonControl
	String sh_input_putrays
	NVAR gsh_flag
	SVAR gsh_path
	sh_putrays(gsh_path,shdata)
End

Function sh_input_getcolumnbutton(sh_input_getcolumn) : ButtonControl
	String sh_input_getcolumn
	NVAR gsh_flag,gsh_column
	SVAR gsh_path,gsh_columnlist
	sh_getshcol(shdata,gsh_column,gsh_flag,"col"+num2str(gsh_column)+"_"+StringFromList(gsh_column-1, gsh_columnlist))
	print "Loaded column#",gsh_column,",", StringFromList(gsh_column-1, gsh_columnlist)
End

Function sh_input_readanglebutton(sh_input_readangle) : ButtonControl
	String sh_input_readangle
	NVAR gsh_flag
	SVAR gsh_path
	sh_readangle(gsh_path,gsh_flag)
End

Function sh_input_2dhistbutton(sh_input_2dhist) : ButtonControl
	String sh_input_2dhist
	sh_2dhist(101,101,"","",1,5,2,1,1,1,1,"")
End

Function sh_input_1dhistbutton(sh_input_1dhist) : ButtonControl
	String sh_input_1dhist
	sh_1dhist(101,"",1,5,2,1,1,"")
End


Function sh_input_closeplotsbutton(sh_input_closeplots) : ButtonControl
	String sh_input_closeplots
	sh_kill_plots("shplot")
End

Function sh_1dhist(numBinx,navex,iFlag,other,histo,minX,maxX,naves)
	Variable numBinx
	String navex
	Variable iflag, other, histo
	Variable maxX, minX
	string naves
	variable whe1,whe2,le
	String/G gnavex_1d,gnaves_1d
	IF(strlen(navex)==0||numBinx==0)
		navex = gnavex_1d
		If(numBinx==0)
			numBinx=101
		Endif
		Prompt numBinx, "Enter number of bins"
		Prompt navex, "Enter the x wave", popup, wavelist("*",";","DIMS:1")
		Prompt iFlag, "Manual limits?", popup, "No;Yes"	
		Prompt other, "Intensity wave?", popup, " No; sPol;pPol; total pol; Input wave"	
		Prompt histo, "Histograms?", popup, "No;Yes"	
		DoPrompt "Values?", numBinx, navex, iFlag, other,histo
		if (V_flag==1)
			return 0
		endif
		gnavex_1d = navex
	Endif
	wave wavex=$navex
	variable lenst1, lenst2
	string navep, navet
	if(other==2 || other==3 || other==4 || other==5)	
		lenst1=strsearch(navex,"_", 0)
		lenst2=strsearch(navex,"_", lenst1+1)
		if(other==2) 
			naves=	ReplaceString(navex[lenst1+1,lenst2-1], navex,"as" ,1)
		elseif(other==3)
			naves=	ReplaceString(navex[lenst1+1,lenst2-1], navex,"ap" ,1)
		elseif(other==4) 
			naves=	ReplaceString(navex[lenst1+1,lenst2-1], navex,"at" ,1)
		elseif(other==5) 
			If(strlen(naves)==0)
				naves = gnaves_1d
				Prompt naves, "Enter the weighting", popup, wavelist("*",";","DIMS:1")
				DoPrompt "naves?",naves
				if (V_flag==1)
					return 0
				endif
				gnaves_1d = naves
			endif
		endif
		wave waves=$naves
	endif	

 	Variable delX
	wavestats/Q wavex
	Variable totalPo=V_npnts
	If(minX==0&&maxX==0)
		minX=V_min
		maxX=v_max
	endif
	if(V_npnts != totalPo)
		DoAlert 0, "Waves with unequal lengths"
		return 0
	endif

	String NewWavex=navex+"_histo"
	Make/O/D/N=(numBinx)  $NewWavex
	wave WewWavex=$NewWavex
	WewWavex=0

	if(Iflag==1)
		wavestats/Q wavex
		minX=V_min
		maxX=V_max
		delX=(V_Max-V_Min)/(numBinx-1)
		SetScale/I x V_min,V_max,"", WewWavex
	else
		If((minX==maxX))
			Prompt minX, "Enter min along x"
			Prompt maxX, "Enter max along x"
			DoPrompt "Values?", minX, maxX
			if (V_flag==1)
				return 0
			endif
		endif
		delX=(MaxX-MinX)/(numBinx-1)
		SetScale/I x MinX,MaxX,"", WewWavex
	endif

	Variable i=0
	Variable inx
	
	i=0
	if(other==2 || other==3 || other==4 || other==5)	
		do
			if(wavex[i]<=maxX && wavex[i]>=minX) 
				inX=round((wavex[i] -minX)/delX)
				WewWavex [inX]+=waves[i]
			endif
			i+=1								// execute the loop body
		while (i<totalPo)				// as long as expression is TRUE
	else
		do
			if(wavex[i]<=maxX && wavex[i]>=minX) 
				inX=round((wavex[i] -minX)/delX)
				WewWavex [inX]+=1
			endif
			i+=1								// execute the loop body
		while (i<totalPo)				// as long as expression is TRUE
	endif

	if (histo==2)
		Display/N=shplot WewWavex
		Label bottom "x"
		Label left "Intensity"
		ModifyGraph standoff=0, tick=2,mirror=2,fSize=14,standoff=1,font="Times New Roman",width=288,height=216
		Wavestats/q/z WewWavex
		Variable good=V_Sum
		Variable sigx=sh_GetStanDev(NewWavex,-inf,inf)
		Variable fwhmx = sh_FindFWHM(NewWavex)
		string stats="\\Z14tot:"+ num2str(good)+"   SD_x:"+num2str(sigx)+"   FWHM_x:"+num2str(fwhmx)
		TextBox/F=0/A=MT/E/X=0/Y=0/B=1 stats
	endif
end

Function sh_2dhist(numBinx,numBinz,navex,navez,iFlag,other,histo,minX,maxX,minZ,maxZ,naves)
	Variable numBinx, numBinz
	String navex
	String navez
	Variable iflag, other, histo
	Variable maxX, maxZ,minX,minZ
	string naves
	
	String/G gnavex_2d,gnavez_2d,gnaves_2d
	variable whe1,whe2,le
	IF(strlen(navex)==0||strlen(navez)==0||numBinx==0||numBinz==0)
		navex = gnavex_2d
		navez = gnavez_2d
		If(numBinx==0)
			numBinx=101
		Endif
		If(numBinz==0)
			numBinz=101
		Endif
		Prompt numBinx, "Enter number of bins x"
		Prompt numBinz, "Enter number of bins z"
		Prompt navex, "Enter the x wave", popup, wavelist("*",";","DIMS:1")
		Prompt navez, "Enter the z wave", popup, wavelist("*",";","DIMS:1")	
		Prompt iFlag, "Manual limits?", popup, "No;Yes"	
		Prompt other, "Intensity wave?", popup, " No; sPol;pPol; total pol; Input wave"	
		Prompt histo, "Histograms?", popup, "No;Both; Hor;Ver"	
		DoPrompt "Values?", numBinx, numBinz,navex, navez, iFlag, other,histo
		if (V_flag==1)
			return 0
		endif
	Endif
	gnavex_2d = navex
	gnavez_2d = navez
//	Print "Wave x:", navex, "    Bins x:", numBinx, "   Wave z:", navez, "   Bins z:", numBinz
	wave wavex=$navex
	wave wavez=$navez
	variable lenst1, lenst2
	string navep, navet
	if(other==2 || other==3 || other==4 || other==5)	
		lenst1=strsearch(navex,"_", 0)
		lenst2=strsearch(navex,"_", lenst1+1)
		if(other==2) 
			naves=	ReplaceString(navex[lenst1+1,lenst2-1], navex,"as" ,1)
		elseif(other==3)
			naves=	ReplaceString(navex[lenst1+1,lenst2-1], navex,"ap" ,1)
		elseif(other==4) 
			naves=	ReplaceString(navex[lenst1+1,lenst2-1], navex,"at" ,1)
		elseif(other==5) 
			If(strlen(naves)==0)
				naves = gnaves_2d
				Prompt naves, "Enter the weighting", popup, wavelist("*",";","DIMS:1")
				DoPrompt "naves?",naves
				if (V_flag==1)
					return 0
				endif
				gnaves_2d = naves
			endif
		endif
//	print naves
	wave waves=$naves
	endif	

 	Variable delX, delZ
	wavestats/Q wavez
	Variable totalPo=V_npnts
	If(minZ==0&&maxZ==0)
		minZ=V_min
		maxZ=v_max
	Endif
	wavestats/Q wavex
	If(minX==0&&maxX==0)
		minX=V_min
		maxX=v_max
	endif
	if(V_npnts != totalPo)
		DoAlert 0, "Waves with unequal lengths"
		return 0
	endif


	String NewWave=navex+navez
	Make/O/D/N=(numBinx, numBinz)  $NewWave
	wave WewWave=$NewWave
	WewWave=0
	String NewWavex=NewWave+"x"
	String NewWavez=NewWave+"z"
	Make/O/D/N=(numBinx)  $NewWavex
	Make/O/D/N=(numBinz)  $NewWavez
	wave WewWavex=$NewWavex
	wave WewWavez=$NewWavez
	WewWavex=0
	WewWavez=0


	if(Iflag==1)
		wavestats/Q wavex
		minX=V_min
		maxX=V_max
		delX=(V_Max-V_Min)/(numBinx-1)
		SetScale/I x V_min,V_max,"", WewWave
		SetScale/I x V_min,V_max,"", WewWavex
		wavestats/Q wavez
		minZ=V_min
		maxZ=V_max
		delZ=(V_Max-V_Min)/(numBinz-1)
		SetScale/I y V_min,V_max,"", WewWave
		SetScale/I x V_min,V_max,"", WewWavez
	else
		If((minX==maxX)||(minZ==maxZ))
			Prompt minX, "Enter min along x"
			Prompt maxX, "Enter max along x"
			Prompt minZ, "Enter min along z"
			Prompt maxZ, "Enter max along z"
			DoPrompt "Values?", minX, maxX,minZ, maxZ
			if (V_flag==1)
				return 0
			endif
		endif
//		Print "minX:", minX, "   maxX:", maxX, "   minZ:", minZ, "   maxZ:",maxZ
		delX=(MaxX-MinX)/(numBinx-1)
		SetScale/I x MinX,MaxX,"", WewWave
		delZ=(MaxZ-MinZ)/(numBinz-1)
		SetScale/I y MinZ,MaxZ,"", WewWave
		SetScale/I x MinX,MaxX,"", WewWavex
		SetScale/I x MinZ,MaxZ,"", WewWavez
	endif

	Variable i=0
	Variable inx
	Variable inz

	
	i=0
	if(other==2 || other==3 || other==4 || other==5)	
		do
			if(wavex[i]<=maxX && wavex[i]>=minX &&wavez[i]<=maxZ && wavez[i]>=minZ) 
				inX=round((wavex[i] -minX)/delX)
				inZ=round((wavez[i] -minZ)/delZ)
				WewWave [inX][inZ]+=waves[i]
				WewWavex [inX]+=waves[i]
				WewWavez [inZ]+=waves[i]
			endif
			i+=1								// execute the loop body
		while (i<totalPo)				// as long as expression is TRUE
	else
		do
			if(wavex[i]<=maxX && wavex[i]>=minX &&wavez[i]<=maxZ && wavez[i]>=minZ) 
				inX=round((wavex[i] -minX)/delX)
				inZ=round((wavez[i] -minZ)/delZ)
				WewWave [inX][inZ]+=1
				WewWavex [inX]+=1
				WewWavez [inZ]+=1
			endif
			i+=1								// execute the loop body
		while (i<totalPo)				// as long as expression is TRUE
	endif
	
	if (histo!=1)
		Display/N=shplot;AppendImage WewWave
		ModifyGraph width=216,height=216
		SetAxis bottom minX,maxX
		SetAxis left minZ,maxZ
		ModifyGraph tick=2
		if (histo==2)
			ModifyGraph margin(top)=50,width=187,height=187
			ModifyGraph axisEnab(left)={0,0.75},axisEnab(bottom)={0,0.75}
			ModifyGraph mirror(bottom)=1
			ModifyGraph mirror(left)=1
			AppendToGraph/L=Hory/B=Horx WewWavex
			ModifyGraph axisEnab(Hory)={0.75,1},axisEnab(Horx)={0,0.75}
			ModifyGraph freePos(Hory)={0,kwFraction},freePos(Horx)={0.75,kwFraction}
			ModifyGraph tick(Hory)=3,noLabel(Hory)=2
			ModifyGraph noLabel(Horx)=2
			ModifyGraph mirror(Hory)=1
		
			AppendToGraph/B=Verx/L=Very/VERT WewWavez
			ModifyGraph axisEnab(Verx)={0.75,1},axisEnab(Very)={0,0.75}
			ModifyGraph freePos(Very)={0.75,kwFraction},freePos(Verx)={0,kwFraction}
			ModifyGraph noLabel(Very)=2, tick(Very)=3
			ModifyGraph tick(Verx)=3,mirror(Verx)=1,noLabel(Verx)=2
			ModifyGraph standoff=0
			ModifyGraph tick(left)=2,tick(bottom)=2
			ModifyGraph rgb=(0,0,0)
		endif
	
		Label left "y";DelayUpdate
		Label bottom "x"
		ModifyGraph standoff=0,margin(top)=36,width=216,height=216
		Wavestats/q/z WewWave
		Variable good=V_Sum
		Variable sigx=sh_GetStanDev(NewWavex,-inf,inf)
		Variable sigz=sh_GetStanDev(NewWavez,-inf,inf)
		Variable fwhmx=sh_FindFWHM(NewWavex)
		Variable fwhmz=sh_FindFWHM(NewWavez)
	//	print good, sigx,sigz 
		string stats="\\Z14\\F'Times New Roman'tot:"+ num2str(good)+"   SD_x:"+num2str(sigx)+"      SD_y:"+num2str(sigz)+"\r"+"FWHM_x:" + num2str(fwhmx)+"     FWHM_y:" + num2str(fwhmz)
		TextBox/F=0/A=MT/E/X=0/Y=0/B=1 stats
		ModifyImage $NewWave ctab= {*,*,Geo,1}
		ModifyGraph fSize=14,font="Times New Roman"
	endif
end

Function sh_GetStanDev(whichWave, xco1, xco2)
//Will get the Standard deviation of a wave. The wave's x needs to be defined.
	String whichWave
	Variable xco1, xco2
	if(strlen(whichwave)==0)
		Prompt whichWave, "Wave to get sigma" , popup, WaveList("*",";","DIMS:1")
		Prompt xco1, "xmin"
		Prompt xco2, "xmax"
		DoPrompt "Wave to get standard deviation", whichWave, xco1,xco2
		if (V_Flag)
			return -1								// User canceled
		endif
	endif
	Wave wav=$whichWave
	Variable i1, i2, i,  index
	Variable ave, sigma
	Wavestats/Q wav
	i1=x2pnt(wav, xco1 )
	i2=x2pnt(wav, xco2 )
	if(i1<0 ||  i2>V_npnts)
		i1=0
		i2=V_npnts
	endIf
	Duplicate/O $whichWave intexxxx, avexx, RMSxx
	RMSxx*=x*x
	avexx*=x
	variable norma, waix, waiz
	norma=area(wav,xco1,xco2)
	variable wai, rmsre
	Variable avera
	avera=area(avexx,xco1,xco2)/norma
	intexxxx*=(x-avera)*(x-avera)
	wai=sqrt(area(intexxxx,xco1,xco2)/norma)
	rmsre=sqrt(area(RMSxx,xco1,xco2)/norma)
	killwaves intexxxx, avexx, RMSxx
	return wai
end

//Project mirror surface to the xz plane of exit pupil function. Assuming mirror x is the same as beam x, no toroid!!!
function hy_mirror_project(wmirror,wlz,wplane)	
	wave wmirror,wlz,wplane
	make/N=(dimsize(wplane,0),dimsize(wplane,1))/O wmirror_projected
	setscale/P x, dimoffset(wplane,0),dimdelta(wplane,0), wmirror_projected
	setscale/P y, dimoffset(wplane,1),dimdelta(wplane,1), wmirror_projected
	
	make/N=(dimsize(wmirror,0),dimsize(wplane,1))/O wmirror_trans
	setscale/P x, dimoffset(wmirror,0),dimdelta(wmirror,0), wmirror_trans
	setscale/P y, dimoffset(wplane,1),dimdelta(wplane,1), wmirror_trans
	
	make/N=(dimsize(wplane,1))/O oneline_z
	setscale/P x, dimoffset(wplane,1),dimdelta(wplane,1), oneline_z
	make/N=(dimsize(wmirror,1))/O oneline_l
	setscale/P x, dimoffset(wmirror,1),dimdelta(wmirror,1), oneline_l
	variable i
	for(i=0;i<dimsize(wmirror,0);i+=1)
		oneline_l = wmirror[i][p]
		oneline_z = oneline_l(wlz(x))
		wmirror_trans[i][]=oneline_z[q]
	endfor
	ImageInterpolate/S={dimoffset(wplane,0),dimdelta(wplane,0),dimoffset(wplane,0)+dimdelta(wplane,0)*(dimsize(wplane,0)-1),dimoffset(wplane,1),dimdelta(wplane,1),dimoffset(wplane,1)+dimdelta(wplane,1)*(dimsize(wplane,1)-1)}/DEST=wmirror_projected Bilinear wmirror_trans
//	ImageInterpolate/S={dimoffset(wplane,0),dimdelta(wplane,0),dimoffset(wplane,0)+dimdelta(wplane,0)*(dimsize(wplane,0)-1),dimoffset(wplane,1),dimdelta(wplane,1),dimoffset(wplane,1)+dimdelta(wplane,1)*(dimsize(wplane,1)-1)}/DEST=wmirror_projected/D=3 Spline wmirror_trans
	killwaves/z wmirror_trans, oneline_z, oneline_l
end


Function hy_CreateCDF1D(wName)
//Create sampling from 2d wave
	String wName
	if(strlen(wName)==0)
		Prompt wName, "Wave to get sigma" , popup, WaveList("*",";","DIMS:1")
		DoPrompt "1D wave", wName
		if (V_Flag)
			return -1								// User canceled
		endif
	endif	
	wave wwName=$wName
	Duplicate/O wwName mDist
	Variable numx
	Variable i	
	numx=DimSize(wwName,0)
	mDist=wwName
	i=1
	do
		mDist[i]+=mDist[i-1]		//mDist matrix contains the rows 					
		i+=1		
	while (i<numx)
	mDist[]/=mDist[numx-1]    //Normalizing each row of the matrix
end

Function hy_MakeDist1D(name)
	string name
	wave wname = $name
	Variable npoints = dimsize(wname,0)
	Variable i
	make/O/D/N=(npoints)  pos_dif
	SetRandomSeed(0.25)			//Call to get the angles and positions
	pos_dif=0
	i=0
	do
		pos_dif[i]=hy_GetOnePoint1D(0)
		i+=1
	while(i<npoints)
end

////////////////////////////////////////////////////////////////////////////////////////////////////
Function hy_GetOnePoint1D(Reset)
	Variable Reset
	Variable resu
	wave  mDist
	variable val
	If (Reset==1)
		SetRandomSeed(0.1)
	endif
	Do
	val=enoise(0.5)+0.5		
	resu=dimoffset(mDist,0)+BinarySearchInterp(mDist,val)*dimdelta(mDist,0)		//Finding vertical x value
	while(NumType(resu) == 2)			// avoid NAN
	return resu
end 

//generate begin.dat file from SPECTRA source size and divergence distribution
Function sh_input_spectra_sourcebutton(sh_input_spectra_source) : ButtonControl
	String sh_input_spectra_source
	string name_spec_size,name_spec_div
	Prompt name_spec_size, "Source size distribution", popup, wavelist("*",";","DIMS:2")
	Prompt name_spec_div, "Source divergence distribution", popup, wavelist("*",";","DIMS:2")
	DoPrompt "Select waves loaded from Spectra", name_spec_size,name_spec_div
	if (V_Flag)
		return -1								// User canceled
	endif
	wave spec_size = $name_spec_size
	wave spec_div = $name_spec_div
	Duplicate/O spec_size root:size_tmp
	Duplicate/O spec_div root:div_tmp
	SetDataFolder root:
	wave size_tmp,div_tmp
	SVAR gsh_path
	NVAR gsh_flag
	sh_readsh(gsh_path,gsh_flag,"begintmp")
	wave begintmp
	//spectra export angle in the unit of mrad, need to change to rad before convoluting with shadow
	setscale/P x, dimoffset(div_tmp,0)*1e-3,dimdelta(div_tmp,0)*1e-3,div_tmp
	setscale/P y, dimoffset(div_tmp,1)*1e-3,dimdelta(div_tmp,1)*1e-3,div_tmp
	sh_spectra_source("size_tmp","div_tmp",begintmp)
	sh_putrays(gsh_path,begintmp)
	killwaves/z size_tmp,div_tmp,begintmp
End

//generate begin.dat file from SPECTRA source size and divergence distribution
Function sh_spectra_source(name_spec_size,name_spec_div,shdata)
	string name_spec_size, name_spec_div
	wave shdata
	sh_getshcol(shdata,1, 0,"onecol")	
	wave onecol
	hy_CreateCDF2D(name_spec_size)
	hy_MakeDist2D("onecol")
	wave xdiv, zdiv
	shdata[0][]=xdiv[q]
	shdata[2][]=zdiv[q]
	hy_CreateCDF2D(name_spec_div)
	hy_MakeDist2D("onecol")
	duplicate/O xdiv stan
	stan = 1/sqrt(1+tan(xdiv)*tan(xdiv)+tan(zdiv)*tan(zdiv))	
	shdata[3][]=tan(xdiv[q])*stan[q]
	shdata[4][]=stan[q]
	shdata[5][]=tan(zdiv[q])*stan[q]
	killwaves/z onecol,mdist,resu,forver,forhor,zdiv,xdiv,stan
end

//function to read spectra output
Function sh_input_spectra_read2dbutton(sh_input_spectra_read2d) : ButtonControl
	String sh_input_spectra_read2d
	sh_spectra_read2d("")
End

Function sh_spectra_read2d(filename)
	string filename
	If (strlen(filename) == 0)
		LoadWave/Q/G/O/D/L={0,0,0,0,3}/N=sptmp
	else
		If(stringmatch(":",filename[strlen(filename)-1]) == 1)
			NewPath/O/Q tmppath, filename
			LoadWave/Q/P=tmppath/G/O/D/L={0,0,0,0,3}/N=sptmp
			print "Spectra file loaded: ", S_path,S_filename 
			KillPath/Z tmppath		
		else
			LoadWave/Q/G/O/D/L={0,0,0,0,3}/N=sptmp filename
			print "Spectra file loaded: ", filename 
		endif
	Endif
	if (V_Flag==0)
		abort							// User canceled
	endif
	string outputname = s_filename[0,strlen(s_filename)-5]
	wave sptmp0,sptmp1,sptmp2
	variable i=0
	do
		i+=1
	while(sptmp1[i+1]==sptmp1[i])
	Redimension/N=(i+1,dimsize(sptmp2,0)/(i+1)) sptmp2
	wavestats/q/z sptmp0
	setscale/I x,v_min,v_max, sptmp2
	wavestats/q/z sptmp1
	setscale/I y,v_min,v_max, sptmp2
	Duplicate/O/D sptmp2 $outputname
	killwaves/z  sptmp0,sptmp1,sptmp2
End

//Generate rays for longitudinally shifted undulator
Function sh_input_shifted_undbutton(sh_input_shifted_und) : ButtonControl
	String  sh_input_shifted_und
	string name_spec_size,name_spec_div
	Prompt name_spec_size, "Source size distribution", popup, wavelist("*",";","DIMS:2")
	Prompt name_spec_div, "Source divergence distribution", popup, wavelist("*",";","DIMS:2")
	DoPrompt "Select waves loaded from Spectra", name_spec_size,name_spec_div
	if (V_Flag)
		return -1								// User canceled
	endif
	wave spec_size = $name_spec_size
	wave spec_div = $name_spec_div
	Duplicate/O spec_size root:size_tmp
	Duplicate/O spec_div root:div_tmp
	SetDataFolder root:
	wave size_tmp,div_tmp
	SVAR gsh_path
	NVAR gsh_flag
	sh_readsh(gsh_path,gsh_flag,"begintmp")
	wave begintmp
	//spectra export angle in the unit of mrad, need to change to rad before convoluting with shadow
	setscale/P x, dimoffset(div_tmp,0)*1e-3,dimdelta(div_tmp,0)*1e-3,div_tmp
	setscale/P y, dimoffset(div_tmp,1)*1e-3,dimdelta(div_tmp,1)*1e-3,div_tmp
	sh_shifted_und(begintmp,"size_tmp","div_tmp",0,0,0,0,0,0)
	killwaves/z size_tmp,div_tmp
	sh_putrays(gsh_path,begintmp)
	killwaves/z begintmp
End

Function sh_shifted_und(shdata,name_spec_size,name_spec_div,esigx,esigz,esigxp,esigzp,longshift,observepoint)
	wave shdata
	string name_spec_size,name_spec_div
	variable esigx,esigz,esigxp,esigzp,longshift,observepoint
	Prompt name_spec_size, "photon size distribution (single e)", popup, wavelist("*",";","DIMS:2")
	Prompt name_spec_div, "photon divergence distribution (single e)", popup, wavelist("*",";","DIMS:2")
	Prompt esigx, "Electron beam size in x (user unit)"
	Prompt esigz, "Electron beam size in z (user unit)"
	Prompt esigxp, "Electron beam divergence (rad) in x"
	Prompt esigzp, "Electron beam divergence (rad) in z"	
	Prompt longshift, "Und center to e center (user unit)"
	Prompt observepoint, "Observe position to e center (user unit)"
	If(strlen(name_spec_size)==0)
		If(esigx<=0)
			DoPrompt "Input parameters",name_spec_size,name_spec_div,esigx,esigz,esigxp,esigzp,longshift,observepoint
		else
			DoPrompt "Input parameters",name_spec_size,name_spec_div
		endif
	else
		If(esigx<=0)
			DoPrompt "Input parameters",esigx,esigz,esigxp,esigzp,longshift,observepoint
		endif
	endif
	//generate rays follow single electron radiation distribution
	sh_getshcol(shdata,1, 0,"onecol")	
	wave onecol
	hy_CreateCDF2D(name_spec_div)
	hy_MakeDist2D("onecol")
	wave xdiv, zdiv
	duplicate/O xdiv xdiv_1
	duplicate/O zdiv zdiv_1
	
	hy_CreateCDF2D(name_spec_size)
	hy_MakeDist2D("onecol")
	duplicate/O xdiv xsize_1
	duplicate/O zdiv zsize_1
	xsize_1 = xdiv+tan(xdiv_1)*(observepoint-longshift)
	zsize_1 = zdiv+tan(zdiv_1)*(observepoint-longshift)

	//generate rays from electron beam distribution
	make/N=(501,501)/D/O egaus_size, egaus_div
	setscale/I x,-esigx*5,esigx*5,egaus_size
	setscale/I y,-esigz*5,esigz*5,egaus_size
	setscale/I x,-esigxp*5,esigxp*5,egaus_div
	setscale/I y,-esigzp*5,esigzp*5,egaus_div
	if(esigx==0)
		egaus_size=exp(-y^2/2/esigz^2)
	elseif (esigz==0)
		egaus_size=exp(-x^2/2/esigx^2)
	else 	
		egaus_size=exp(-x^2/2/esigx^2)*exp(-y^2/2/esigz^2)
	endif
	if(esigxp==0)
		egaus_div=exp(-y^2/2/esigzp^2)
	elseif (esigzp==0)
		egaus_div=exp(-x^2/2/esigxp^2)
	else 	
		egaus_div=exp(-x^2/2/esigxp^2)*exp(-y^2/2/esigzp^2)
	endif	
	hy_CreateCDF2D("egaus_div")
	hy_MakeDist2D("onecol")
	duplicate/O xdiv xdiv_2,xdiv_tot
	duplicate/O zdiv zdiv_2,zdiv_tot
	xdiv_tot = xdiv_1+xdiv_2
	zdiv_tot = zdiv_1+zdiv_2
	hy_CreateCDF2D("egaus_size")
	hy_MakeDist2D("onecol")
	duplicate/O xdiv xsize_tot
	duplicate/O zdiv zsize_tot
	xsize_tot = xsize_1+xdiv+tan(xdiv_2)*observepoint
	zsize_tot = zsize_1+zdiv+tan(zdiv_2)*observepoint
	duplicate/O xdiv stan	
	//save in to rays
	shdata[0][]=xsize_tot[q]
	shdata[2][]=zsize_tot[q]
	stan = 1/sqrt(1+tan(xdiv_tot)*tan(xdiv_tot)+tan(zdiv_tot)*tan(zdiv_tot))	
	shdata[3][]=tan(xdiv_tot[q])*stan[q]
	shdata[4][]=stan[q]
	shdata[5][]=tan(zdiv_tot[q])*stan[q]
	
	killwaves/z onecol,mdist,resu,forver,forhor,zdiv,xdiv,stan,xdiv_1,zdiv_1,xdiv_2,zdiv_2,xsize_1,zsize_1,xdiv_tot,zdiv_tot,xsize_tot,zsize_tot,egaus_div,egaus_size
End

Function hy_CreateCDF2D(Name)
//Create wave mDist with a sampling of a sampling of 2d wave
//Has the same number of points as the original wave
//It is normalized to 1
//	wparName={energy, dis, numx, offsetx, deltx, numy, offsety, delty, aperh, aperv,NumberP} 
	String Name
	if(strlen(Name)==0)
		Prompt Name, "Wave to use" , popup, WaveList("*",";","DIMS:2")
		DoPrompt "2D wave", Name
		if (V_Flag)
			return -1								// User canceled
		endif
	endif	
	wave wName=$Name
	Duplicate/O wName mDist
	Make/O/N=2/D resu  //Creates the wave used to transfer results. Used in next step
	Variable numx, numy
	Variable i, j, norma	
	numx=dimsize(wName,0)
	numy=dimsize(wName,1)
 	Make/O/N=(numy) ForVer				//Waves for the inversion of the divergences
	SetScale/P x dimoffset(wName,1),dimdelta(wName,1),"", ForVer
	Make/O/N=(numx) ForHor
	SetScale/P x dimoffset(wName,0),dimdelta(wName,0),"", ForHor

	ForVer=0
	mDist=wName
	i=1
	j=0
	do					//Each row summed by previous value
		do
			mDist[i][j]+=mDist[i-1][j]		//mDist matrix contains the rows 					
			i+=1		
		while (i<numx)
		i=1
		j+=1
	while(j<numy)				// as long as expression is TRUE

	ForVer=mDist[numx-1][p]
	j=1
	do					//Sum previous element
		ForVer[j]+=ForVer[j-1]				//ForVer contains a vector with distribution
		j+=1
	while(j<numy)
	ForVer/=ForVer[numy-1]
	mDist[][]/=mDist[numx-1][q]     //Normalizing each row of the matrix

end
////////////////////////////////////////////////////////////////////////////////////////////////////
Function hy_MakeDist2D(name)
//Will generate the distribution as 
// Calls GetOnePoint
	String name
	wave wName=$Name
	Variable nPoints=dimsize(wname,0)
	wave resu
	Variable i

	make/O/N=(npoints) xDiv, zDiv
	i=0
	do
		hy_GetOnePoint2D("mDist",Resu, 0)
		xDiv[i] =Resu[0]
		zDiv[i] =Resu[1]
		i+=1
	while(i<npoints)
end

////////////////////////////////////////////////////////////////////////////////////////////////////
Function hy_GetOnePoint2D(Name,  resu,Reset)
	String Name
	wave resu
	Variable Reset
	wave  ForVer, ForHor
	If (Reset==1)
		SetRandomSeed(0.1)
	endif
	wave wavem=$name
	variable xDiv, zDiv, pointNumber
	Variable offsetx=dimoffset(wavem,0)
	Variable deltx=dimdelta(wavem,0)
	Variable offsety=dimoffset(wavem,1)
	Variable delty=dimdelta(wavem,1)

	//Random numbers 0 to1
	xDiv=enoise(0.5)+0.5			
	zDiv=enoise(0.5)+0.5			

	if (zDiv<=ForVer[0])
		resu[1]=offsety
	else
		resu[1]=BinarySearchInterp(ForVer, zDiv)		//Finding vertical x value
		pointNumber=round(resu[1])
		resu[1]=offsety+resu[1]*delty
	endif
	ForHor=wavem[p][pointNumber]	//Finding the horizontal angle 
	if (xDiv<=ForHor[0])
		resu[0]=offsetx
	else
		resu[0]=offsetx+deltx*BinarySearchInterp(ForHor, xDiv)
	endif

	if(reset==1)
		print resu[0],  resu[1], resu[2], resu[3]
	endif
end 

//Apr. 7th, 2016 include slo1 as input
Function/S hy_CreateSurfaceFile_range_new(name,flag,he,slo1,npo,del,freq_min,freq_max,randomseed)
	String name
	string flag	//"se", slope error, "he", height error
	variable he,slo1
	Variable npo	//=190		//Number of points surface wave
	Variable del	//=1			//Spacing surface wave
	variable freq_min
	variable freq_max
	Variable RandomSeed	//=0.1
	Variable nFreq = freq_max-freq_min+1	//=50
	
	variable mult1= 1e-10
	If(slo1==0)
		slo1=-3.0
	endif
	
	If(strlen(name)==0)	
		Prompt name, "Name of wave to create"
		Prompt flag, "slope error or height error",popup "se;he"
		prompt he, "rms error (mm or rad)"
		prompt slo1, "log(PSD) vs log(f) slope, default:-3"
		Prompt npo, "Enter number of points, even"
		Prompt del, "Enter delta value"
		Prompt freq_min, "Lowest frequency (>=1)"
		Prompt freq_max, "Highest frequency"
		Prompt RandomSeed, "Random seed between 0 and 1"
		doPrompt "Input", name,flag,he,slo1,npo, del, freq_min, freq_max, RandomSeed
		if (V_Flag)
			return ""								// User canceled
		endif
	endif
	
	If(strlen(name)==0)
		name="mirror"
	endif
	SetRandomSeed RandomSeed
	Make/N=(npo)/O/D $Name
	Wave wName=$Name
	Variable length=npo*del
	SetScale/P x -length/2, del, "", wName

	Variable freq=npo/(length*npo+1)
	Make/N=(nFreq)/O/D , FouAmp,FouFre,FouPha
	SetScale/P x freq*freq_min,freq,"",  FouAmp,FouFre,FouPha
	FouFre=x
	Variable i
	for (i=0;i<nFreq;i+=1)
		FouAmp[i]=mult1*FouFre[i]^(slo1/2)
	endfor	
	variable fileNumber
	wName=0
	for (i=0;i<nFreq;i+=1)
		FouPha[i] =  enoise(pi)
		wName += FouAmp[i]*cos(-pi*2*x*FouFre[i]+FouPha[i]);
	endfor
	variable he_cal 
	If(stringmatch(flag,"he")==1)
		he_cal = hy_findrmserror(Name,0)
	elseif(stringmatch(flag,"se")==1)
		he_cal = hy_findrmsslopefromheight(Name,0)
	endif
	wName*=he/he_cal
	killwaves/z FouPha,FouFre,FouAmp
	return name
end

Function hy_CreateSurfaceFile_range(name,npo,del,freq_min,freq_max,randomseed)
	String name
	Variable npo	//=190		//Number of points surface wave
	Variable del	//=1			//Spacing surface wave
	variable freq_min
	variable freq_max
	Variable RandomSeed	//=0.1
	Variable nFreq = freq_max-freq_min+1	//=50
		
//	Variable mult1=2.1e-10
//	Variable mult2=mult1
//	Variable slo1=-1.5
//	Variable slo2= slo1
//	Variable chSlo=0.001
	variable mult1= 1e-10
	Variable mult2=mult1*5
	variable slo1 = -2.3		//slope of the log_psd vs log_frequency
	Variable slo2= -0.9	
	Variable chSlo=0.1

	If(strlen(name)==0)	
		Prompt name, "Name of wave to create"
		Prompt npo, "Enter number of points, even"
		Prompt del, "Enter delta value"
		Prompt freq_min, "Lowest frequency (>=1)"
		Prompt freq_max, "Highest frequency"
		Prompt RandomSeed, "Random seed between 0 and 1"
		doPrompt "Input", name,npo, del, freq_min, freq_max, RandomSeed
		if (V_Flag)
			return -1								// User canceled
		endif
	endif
	
	SetRandomSeed RandomSeed
	Make/N=(npo)/O/D $Name
	Wave wName=$Name
	Variable length=npo*del
	SetScale/P x -length/2, del, "", wName

	Variable freq=npo/(length*npo+1)
	Make/N=(nFreq)/O/D , FouAmp,FouFre,FouPha
	SetScale/P x freq*freq_min,freq,"",  FouAmp,FouFre,FouPha
	FouFre=x
	Variable i
	for (i=0;i<nFreq;i+=1)
		if(FouFre[i]<chSlo)
			FouAmp[i]=mult1*FouFre[i]^(slo1/2)	//Mar 2016, changed from slo1 to slo1/2, then slo1 is the slope of the log_PSD vs log_frequency
		else
			FouAmp[i]=mult2*FouFre[i]^(slo2/2)
		endif
	endfor	
	variable fileNumber
	wName=0
	for (i=0;i<nFreq;i+=1)
		FouPha[i] =  enoise(pi)
		wName += FouAmp[i]*cos(-pi*2*x*FouFre[i]+FouPha[i]);
	endfor	
	killwaves/z FouPha,FouFre,FouAmp
end

Function hy_findrmserror(Name,flag)
	String name
	variable flag	//0 no print result, !=0 print result in history
	duplicate/O $name wmirror_tmp1
	If(mod(dimsize(wmirror_tmp1,0),2)==1)
		DeletePoints dimsize(wmirror_tmp1,0)-1,1, wmirror_tmp1		//delete one point if odd number of points
	endif
	FFT/OUT=3/DEST=wfftcol wmirror_tmp1
	Duplicate/O wfftcol, waPSD
	waPSD = 2*dimdelta(wmirror_tmp1,0)*wfftcol^2/dimsize(wmirror_tmp1,0)
	//based on the reference, the first and the last point need to be divided by two.
	//We are not sure about this. 
	//The first point contains the height average information. If the height average is subtracted before calling the function,
	//these two points are very small numbers and the following steps do negligible effects.
	waPSD[0]/=2
	waPSD[dimsize(waPSD,0)-1]/=2
	
	Duplicate/O waPSD waRMS
	integrate/T waRMS
	waRMS=sqrt(waRMS)
	variable rmserror = waRMS[dimsize(waRMS,0)-1]
	If(flag!=0)
		print "The rms error is:", rmserror
	endif
	killwaves/z wmirror_tmp1, wfftcol,waPSD,waRMS
	return rmserror
End

Function hy_findrmsslopefromheight(Name,flag)
	String name
	variable flag	//0 no print result, !=0 print result in history
	duplicate/O $name wmirror_tmp
	wavestats/q/z wmirror_tmp
	wmirror_tmp-=v_avg
	Differentiate/METH=2 wmirror_tmp
	variable slopeerror = hy_findrmserror("wmirror_tmp",flag)
	killwaves/z wmirror_tmp
	return slopeerror
End

Function hy_findrmsheightfromslope(Name,flag)
	String name
	variable flag	//0 no print result, !=0 print result in history
	duplicate/O $name wmirror_tmp
	Integrate/T wmirror_tmp
	wavestats/q/z wmirror_tmp
	wmirror_tmp-=v_avg
	variable heighterror = hy_findrmserror("wmirror_tmp",flag)
	killwaves/z wmirror_tmp
	return heighterror
End

Function hy_findrmsslope_notrecommended(Name,flag)
	String name
	variable flag	//0 no print result, !=0 print result in history
	duplicate/O $name wmirror_tmp
	If(mod(dimsize(wmirror_tmp,0),2)==1)
		DeletePoints dimsize(wmirror_tmp,0)-1,1, wmirror_tmp
	endif
	wavestats/q/z wmirror_tmp
	wmirror_tmp-=v_avg
	FFT/OUT=3/DEST=wfftcol wmirror_tmp
	Duplicate/O wfftcol, waPSD, wsPSD
	waPSD = 2*dimdelta(wmirror_tmp,0)*wfftcol^2/dimsize(wmirror_tmp,0)
	waPSD[0]/=2
	waPSD[dimsize(waPSD,0)-1]/=2
	
	wsPSD = waPSD[p]*(2*pi*(p-1)/dimsize(wmirror_tmp,0)/dimdelta(wmirror_tmp,0))^2
	Duplicate/O wsPSD wsRMS
	integrate/T wsRMS
	variable rmsslope = sqrt(wsRMS[dimsize(wsRMS,0)-1])
	If(flag!=0)
		print "The rms slope error is:", rmsslope
	endif
	killwaves/z wmirror_tmp, wfftcol,waPSD,waRMS,wsPSD,wsRMS
	return rmsslope
End

//Function hy_FindrmsSlope(Name,ty)
//	String name,ty
//	String options="Hanning;none;Bartlett"
//	if (strlen(name)==0)
//		Prompt name, "Name of wave with figure profile",popup,WaveList("*",";","DIMS:1")
//		Prompt ty, "Filter to apply",popup, options
//		doPrompt "Name", name,ty
//		if (V_Flag)
//			return -1								// User canceled
//		endif
//	endif
//	wave wHeight_o=$name
//	duplicate/O/D wHeight_o wHeight
//	wavestats/Q wHeight
//	Variable npHeight=V_npnts					//Number of points original wave
//	Variable delwHeight=DimDelta(wHeight,0)		//Step of height wave
//	Variable offwHeight=DimOffset(wHeight,0)
//	if(mod(npHeight,2)==1)						//Odd number of points
//		DeletePoints 0,1, wHeight
//		SetScale/P x offwHeight+delwHeight, delwHeight,"", wHeight
//		npHeight-=1
//	endif
//	Variable lenHeight=npHeight*delwHeight
//	
//	string Fou=name+"_Fou"
//	Duplicate/O wHeight $Fou
//	wave wfou=$Fou
//	strswitch(ty)						// string switch
//		case "None":
//			break
//		case "Hanning":
//			WindowFunction Hanning, wfou;  wfou*=2					//Hanning
//			name=name+"_H"
//			break
//		case "Bartlett":
//			WindowFunction Bartlett, wfou;  wfou*=2					//Hanning
//			name=name+"_B"
//			break
//	endswitch
//	FFT wfou
//	wavestats/Q wfou
//	Variable npFou=V_npnts
//	
//	String Amp=name+"_Amp"
//	String Pha=name+"_Pha"
//	String aPSD=name+"_aPSD"
//	String aRMS=name+"_aRMS"
//	String sPSD=name+"_sPSD"
//	String sRMS=name+"_sRMS"
//	
//	Duplicate/O wfou $Amp, $Pha, $aPSD, $aRMS, $sPSD, $sRMS
//	Redimension/R $Amp,     $Pha, $aPSD, $aRMS, $sPSD, $sRMS
//	wave wAmp=$Amp
//	wave wPha=$Pha
//	wave waPSD=$aPSD
//	wave waRMS=$aRMS
//	wave wsPSD=$sPSD
//	wave wsRMS=$sRMS
//	
//	wAmp=2/npHeight*Real(r2polar(wFou))				//Igor FFT Amplitude scaling
//	wAmp[0]=1/npHeight*Real(r2polar(wFou[0]))			//Igor FFT Amplitude scaling
//	wPha=Imag(r2polar(wFou))
//	if(wAmp[0] <1e-20)
//		wAmp[0]=wAmp[1]
//	endif
//
//	waPSD=2*delwHeight*Magsqr(wFou)/npHeight
//	if(waPSD[0] <1e-20)
//		waPSD[0]=waPSD[1]
//	endif
//
//	waRMS = waPSD
//	Integrate/T waRMS
// 	waRMS=sqrt(waRMS)
//	
//	wsPSD[0]=0
//	Variable i
//	for (i=1;i<npFou;i+=1)
//		wsPSD[i]=	(2*pi*(i-1)/(npHeight*delwHeight))^2*waPSD[i]
//	endfor
//	wsRMS=2*pi^2*wAmp^2*x^2*lenHeight
//	Integrate/T wsRMS
// 	wsRMS=sqrt(wsRMS)
//	variable rmsslope = wsRMS[npFou-1]
//	killwaves/z wfou,wamp,wpha,wapsd,wspsd,warms,wsrms,wHeight
//	return rmsslope
//end
//
//Function hy_Findrmsheight(Name,ty)
//	String name,ty
//	String options="Hanning;none;Bartlett"
//	if (strlen(name)==0)
//		Prompt name, "Name of wave with figure profile",popup,WaveList("*",";","DIMS:1")
//		Prompt ty, "Filter to apply",popup, options
//		doPrompt "Name", name,ty
//		if (V_Flag)
//			return -1								// User canceled
//		endif
//	endif
//	wave wHeight_o=$name
//	Duplicate/O/D wHeight_o wHeight
//	wavestats/Q wHeight
//	Variable npHeight=V_npnts					//Number of points original wave
//	Variable delwHeight=DimDelta(wHeight,0)		//Step of height wave
//	Variable offwHeight=DimOffset(wHeight,0)
//	if(mod(npHeight,2)==1)						//Odd number of points
//		DeletePoints 0,1, wHeight
//		SetScale/P x offwHeight+delwHeight, delwHeight,"", wHeight
//		npHeight-=1
//	endif
//	Variable lenHeight=npHeight*delwHeight
//	
//	string Fou=name+"_Fou"
//	Duplicate/O wHeight $Fou//,xvalue
//	wave wfou=$Fou
//
//	strswitch(ty)						// string switch
//		case "None":
//			break
//		case "Hanning":
//			WindowFunction Hanning, wfou;  wfou*=2					//Hanning
//			name=name+"_H"
//			break
//		case "Bartlett":
//			WindowFunction Bartlett, wfou;  wfou*=2					//Hanning
//			name=name+"_B"
//			break
//	endswitch
//	FFT wfou
//	wavestats/Q wfou
//	Variable npFou=V_npnts
//	
//	String Amp=name+"_Amp"
//	String Pha=name+"_Pha"
//	String aPSD=name+"_aPSD"
//	String aRMS=name+"_aRMS"
//	String sPSD=name+"_sPSD"
//	String sRMS=name+"_sRMS"
//	
//	Duplicate/O wfou $Amp, $Pha, $aPSD, $aRMS, $sPSD, $sRMS
//	Redimension/R $Amp,     $Pha, $aPSD, $aRMS, $sPSD, $sRMS
//	wave wAmp=$Amp
//	wave wPha=$Pha
//	wave waPSD=$aPSD
//	wave waRMS=$aRMS
//	wave wsPSD=$sPSD
//	wave wsRMS=$sRMS
//	
//	wAmp=2/npHeight*Real(r2polar(wFou))				//Igor FFT Amplitude scaling
//	wAmp[0]=1/npHeight*Real(r2polar(wFou[0]))			//Igor FFT Amplitude scaling
//	wPha=Imag(r2polar(wFou))
//	if(wAmp[0] <1e-20)
//		wAmp[0]=wAmp[1]
//	endif
//
//	waPSD=2*delwHeight*Magsqr(wFou)/npHeight
//	if(waPSD[0] <1e-20)
//		waPSD[0]=waPSD[1]
//	endif
//
//	waRMS = waPSD
//	Integrate/T waRMS
// 	waRMS=sqrt(waRMS)
//		
//	wsPSD[0]=0
//	Variable i
//	for (i=1;i<npFou;i+=1)
//		wsPSD[i]=	(2*pi*(i-1)/(npHeight*delwHeight))^2*waPSD[i]
//	endfor
//	wsRMS=2*pi^2*wAmp^2*x^2*lenHeight
//	Integrate/T wsRMS
// 	wsRMS=sqrt(wsRMS)
//
//	variable rmsheight = waRMS[npFou-1]
//	killwaves/z wfou,wamp,wpha,wapsd,wspsd,warms,wsrms,wHeight
//	return rmsheight
//end

Function hy_GetStanDev(whichWave, xco1, xco2)
//Will get the Standard deviation of a wave. The wave's x needs to be defined.
	String whichWave
	Variable xco1, xco2
	if(strlen(whichwave)==0)
		Prompt whichWave, "Wave to get sigma" , popup, WaveList("*",";","DIMS:1")
		Prompt xco1, "xmin"
		Prompt xco2, "xmax"
		DoPrompt "Wave to get standard deviation", whichWave, xco1,xco2
		if (V_Flag)
			return -1								// User canceled
		endif
	endif
	Wave wav=$whichWave
	Variable i1, i2, i,  index
	Variable ave, sigma
	Wavestats/Q wav
	i1=x2pnt(wav, xco1 )
	i2=x2pnt(wav, xco2 )
	if(i1<0 ||  i2>V_npnts)
		i1=0
		i2=V_npnts
	endIf
	Duplicate/O $whichWave intexxxx, avexx, RMSxx
	RMSxx*=x*x
	avexx*=x
	variable norma, waix, waiz
	norma=area(wav,xco1,xco2)
	variable wai, rmsre
	Variable avera
	avera=area(avexx,xco1,xco2)/norma
	intexxxx*=(x-avera)*(x-avera)
	wai=sqrt(area(intexxxx,xco1,xco2)/norma)
	rmsre=sqrt(area(RMSxx,xco1,xco2)/norma)
	killwaves intexxxx, avexx, RMSxx
	return wai
end

Function sh_FindFWHM(name)
	String name
	if (strlen(name)==0)
		Prompt name, "Enter the wave", popup, wavelist("*",";","")
		DoPrompt "", name
	endif
	variable FWHM
	wavestats/Q $name
	FindLevels/d=levels/Q $name, V_Max/2
	wavestats/Q levels
	FWHM=v_max-v_min
	killwaves/z levels
	return FWHM
end

Function sh_kill_plots(graphnameprefix)
	String graphnameprefix
	If (strlen(graphnameprefix)==0)
		graphnameprefix = "Graph"
	Endif
	graphnameprefix+="*"
	String graphall
	graphall = winlist(graphnameprefix,";","")
	Variable i
	Do
		execute/q/z "killwindow "+StringFromList(i, graphall)
		i+=1
	While (strlen(StringFromList(i, graphall))!=0 && strlen(StringFromList(i, graphall))!=nan)
End

Function hy_showplots(hy_input_showplots) : ButtonControl
	String hy_input_showplots
	NVAR/Z ghy_diff_plane,ghy_nf,ghy_lengthunit
	wave/Z xx_image_ff_histo,xx_image_nf_histo,zz_image_ff_histo,zz_image_nf_histo,xx_image_ffzz_image_ff,xx_image_ffzz_image_ffx,xx_image_ffzz_image_ffz
	Switch(ghy_diff_plane)
		case 1:
			Display/N=hyplot xx_image_ff_histo
			ModifyGraph axisOnTop=1,tick=2,mirror=2,fSize=14,standoff=0,notation=1,font="Times New Roman";DelayUpdate
			ModifyGraph margin(left)=43,margin(bottom)=43,margin(top)=14,margin(right)=14,width=288,height=216
			Label left "Intensity (far-field)";DelayUpdate
			Label bottom "X ("+StringFromList(ghy_lengthunit-1, "cm;mm")+")"
			If(ghy_nf==1)
				Display/N=hyplot xx_image_nf_histo
				ModifyGraph axisOnTop=1,tick=2,mirror=2,fSize=14,standoff=0,notation=1,font="Times New Roman";DelayUpdate
				ModifyGraph margin(left)=43,margin(bottom)=43,margin(top)=14,margin(right)=14,width=288,height=216
				Label left "Intensity (near-field)";DelayUpdate
				Label bottom "X ("+StringFromList(ghy_lengthunit-1, "cm;mm")+")"
			endif
			break
		case 2:
			Display/N=hyplot zz_image_ff_histo
			ModifyGraph axisOnTop=1,tick=2,mirror=2,fSize=14,standoff=0,notation=1,font="Times New Roman";DelayUpdate
			ModifyGraph margin(left)=43,margin(bottom)=43,margin(top)=14,margin(right)=14,width=288,height=216
			Label left "Intensity (far-field)";DelayUpdate
			Label bottom "Z ("+StringFromList(ghy_lengthunit-1, "cm;mm")+")"
			If(ghy_nf==1)
				Display/N=hyplot zz_image_nf_histo
				ModifyGraph axisOnTop=1,tick=2,mirror=2,fSize=14,standoff=0,notation=1,font="Times New Roman";DelayUpdate
				ModifyGraph margin(left)=43,margin(bottom)=43,margin(top)=14,margin(right)=14,width=288,height=216
				Label left "Intensity (near-field)";DelayUpdate
				Label bottom "Z ("+StringFromList(ghy_lengthunit-1, "cm;mm")+")"
			endif		
			break
		case 3:
//			Display/N=hyplot;AppendImage xx_image_ffzz_image_ff
//			ModifyImage xx_image_ffzz_image_ff ctab= {*,*,Geo,1}
//			ModifyGraph axisOnTop=1,tick=2,fSize=14,standoff=0,notation=1,font="Times New Roman"
//			ModifyGraph width=288,height=216,margin(left)=50,margin(bottom)=43,margin(top)=14,margin(right)=14
//			Label left "X (user unit)"
//			Label bottom "Z (user unit)"
//			Display/N=hyplot xx_image_ffzz_image_ffz
//			ModifyGraph axisOnTop=1,tick=2,mirror=2,fSize=14,standoff=0,notation=1,font="Times New Roman";DelayUpdate
//			ModifyGraph margin(left)=43,margin(bottom)=43,margin(top)=14,margin(right)=14,width=288,height=216
//			Label left "Intensity (far-field)";DelayUpdate
//			Label bottom "Z (user unit)"
//			Display/N=hyplot xx_image_ffzz_image_ffx
//			ModifyGraph axisOnTop=1,tick=2,mirror=2,fSize=14,standoff=0,notation=1,font="Times New Roman";DelayUpdate
//			ModifyGraph margin(left)=43,margin(bottom)=43,margin(top)=14,margin(right)=14,width=288,height=216
//			Label left "Intensity (far-field)";DelayUpdate
//			Label bottom "X (user unit)"
			Display/N=hyplot;AppendImage xx_image_ffzz_image_ff
			ModifyGraph tick=2,axisOnTop=1,fSize=14,standoff=0,notation=1,font="Times New Roman"
			ModifyGraph width=216,height=216,margin(left)=50,margin(bottom)=43,margin(top)=14,margin(right)=14
			ModifyGraph axisEnab(left)={0,0.75},axisEnab(bottom)={0,0.75},mirror(bottom)=1, mirror(left)=1
			AppendToGraph/L=Hory/B=Horx xx_image_ffzz_image_ffx
			ModifyGraph axisEnab(Hory)={0.75,1},axisEnab(Horx)={0,0.75}
			ModifyGraph freePos(Hory)={0,kwFraction},freePos(Horx)={0.75,kwFraction}
			ModifyGraph tick(Hory)=3,noLabel(Hory)=2,noLabel(Horx)=2,mirror(Hory)=1
			AppendToGraph/B=Verx/L=Very/VERT xx_image_ffzz_image_ffz
			ModifyGraph axisEnab(Verx)={0.75,1},axisEnab(Very)={0,0.75}
			ModifyGraph freePos(Very)={0.75,kwFraction},freePos(Verx)={0,kwFraction}
			ModifyGraph noLabel(Very)=2, tick(Very)=3
			ModifyGraph tick(Verx)=3,mirror(Verx)=1,noLabel(Verx)=2
			ModifyGraph standoff=0, tick(left)=2,tick(bottom)=2,rgb=(0,0,0)
			Label left "Z ("+StringFromList(ghy_lengthunit-1, "cm;mm")+")"
			Label bottom "X ("+StringFromList(ghy_lengthunit-1, "cm;mm")+")"
			SetAxis bottom dimoffset(xx_image_ffzz_image_ff,0),dimoffset(xx_image_ffzz_image_ff,0)+dimdelta(xx_image_ffzz_image_ff,0)*(dimsize(xx_image_ffzz_image_ff,0)-1)
			SetAxis left  dimoffset(xx_image_ffzz_image_ff,1),dimoffset(xx_image_ffzz_image_ff,1)+dimdelta(xx_image_ffzz_image_ff,1)*(dimsize(xx_image_ffzz_image_ff,1)-1)
			ModifyImage xx_image_ffzz_image_ff ctab= {*,*,Geo,1}
			break
	endswitch
End