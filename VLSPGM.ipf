#pragma rtGlobals=3		// Use modern global access method.

Menu "Macros"
	Submenu "Gratings"
		Submenu "VLSPGM"
			"Initialize machine", FillSR()
			"Initialize globals, find bs", FindBs()
			"Calc mono", CalcAll()
			"Show Values", ShowVal()
			"Get Parameters for RayTracing", GetParRayTrace()
			"CreateOrUpdateCVal", CreateOrUpdateCVal()
		end
	end
end


//__________________________________________________________________________________________
Function f20PG(w,x)
//Solve for b2
	Wave w
	Variable x
	//w[1]= dSoGr
	//w[3]=dGrEx
	//w[4]=order
	//w[5]==k
	//w[6]=energy
	return cosd(w[0])^2/w[1]+ cosd(w[2])^2/w[3]+2*w[4]*w[5]*eV_to_mmF(w[6])*x
end

//__________________________________________________________________________________________
Function f30PG(w,x)
//Solve for b3
	Wave w
	Variable x
	//w[1]= dSoGr
	//w[3]=dGrEx
	//w[4]=order
	//w[5]==k
	//w[6]=energy
	return Sind(w[0])*cosd(w[0])^2/w[1]^2+ sind(w[2])*cosd(w[2])^2/w[3]^2+2*w[4]*w[5]*eV_to_mmF(w[6])*x
end

//__________________________________________________________________________________________
Function f20PG1(w,x,y)
//Solve for alpha and beta
	Wave w
	Variable x, y
	//w[0]=dGrEx
	//w[1]=order
	//w[2]=k
	//w[3]=energy
	//w[4]=b2
	Variable dSoGr
	dSoGr=fdSoGr(x, y)
	return cosd(x)^2/dSoGr+ cosd(y)^2/w[0]+2*w[1]*w[2]*eV_to_mmF(w[3])*w[4]
end

//__________________________________________________________________________________________
Function GrEq(w,x,y)
//Solve for alpha and beta, grating equation
	Wave w
	Variable x, y
	//w[0]=dGrEx
	//w[1]=order
	//w[2]=k
	//w[3]=energy
	//w[4]=b2
	return w[1]*w[2]*eV_to_mmF(w[3])-sind(x)-sind(y)
end

//__________________________________________________________________________________________
Function findSlit(w,x)
//Find sllit for sToRe
	Wave w
	Variable x
	Variable ret
	//w[0]= lam
	//w[1]=bet
	//w[2]=lmm
	//w[3]=dGrEx
	//w[4]=energy
	//w[5]=index
	NVAR sToRe
	wave rEnTa
	wave rSEGRTa
	wave rSEPMTa
	wave Energies
	Variable slitRes
	Variable i=w[5]
	slitRes=RlEx (w[0],w[1],w[2],x,w[3])
	ret=1/sToRe-sqrt(slitRes^2+rEnTa[i]^2+rSEGRTa[i]^2+rSEPMTa[i]^2)/energies[i]
//	print i, slitRes, Energies[i], rEnTa[i], rSEGRTa[i],rSEPMTa[i],ret
	return ret
end


//__________________________________________________________________________________________
Function fdM2Gr(alp, bet)
//Calculates the d between M2 and grating
	Variable alp, bet
	NVar dHe=root:SRCalc:dHe
	Variable angam
	angam=(alp-bet)
	return dHe/(Sind(alp-bet))	
end

//__________________________________________________________________________________________
Function fdSoGr(alp, bet)
//Calculates the d between source and grating
	Variable alp, bet
	NVar dHe=root:SRCalc:dHe
	NVar dSoGrX=root:SRCalc:dSoGrX
	Variable angam
	angam=(alp-bet)
	return dSoGrX+dHe*(1/(Sind(angam))+1/Tand(angam))	
end
//__________________________________________________________________________________________
Function sigUn(ener,xy)
//Sigma total electron +ID
	Variable ener
	Variable xy
	NVar sigx=root:SRCalc:SigmaX
	NVar sigy=root:SRCalc:SigmaY
	NVar unLe=root:SRCalc:dUnLe
	if (xy==0)
		return sqrt(sigx^2+eV_to_mmF(ener)*unLe/(2*pi^2))
	else
		return sqrt(sigy^2+eV_to_mmF(ener)*unLe/(2*pi^2))
	endif	
end
//__________________________________________________________________________________________
Function sigUnP(ener,xy)
//Sigma total electron +ID divergence
	Variable ener
	Variable xy
	NVar sigxp=root:SRCalc:SigmaXP
	NVar sigyp=root:SRCalc:SigmaYP
	NVar unLe=root:SRCalc:dUnLe
	if (xy==0)
		return sqrt(sigxp^2+eV_to_mmF(ener)/(2*unLe))
	else
		return sqrt(sigyp^2+eV_to_mmF(ener)/(2*unLe))
	endif	
end

//__________________________________________________________________________________________
Function FillSR()
//Initialize machine
//	SelectMachine()
	Variable sigx=NumVarOrDefault("root:SRCalc:sigmaX", 0.1) 
	Variable sigy=NumVarOrDefault("root:SRCalc:sigmaY", 0.01) 
	Variable sigxp=NumVarOrDefault("root:SRCalc:sigmaXp", 1e-5) 
	Variable sigyp=NumVarOrDefault("root:SRCalc:sigmaYp", 3e-6) 
	Variable UnLe=NumVarOrDefault("root:SRCalc:dUnLe", 4000) 
	Variable V_Flag
	Prompt sigx, "Sigma x mm"
	Prompt sigy, "Sigma y mm"
	Prompt sigxp, "Sigma x divergence mradian"
	Prompt sigyp, "Sigma y divergence mradian"
	Prompt UnLe, "ID length mm"
	doPrompt "Electron sigmas", sigx,sigy,sigxp,sigyp, UnLe
	if (V_Flag)
		return -1								// User canceled
	endif
	Variable/G root:SRCalc:sigmaX=sigx
	Variable/G root:SRCalc:sigmaY=sigy
	Variable/G root:SRCalc:sigmaXp=sigxp
	Variable/G root:SRCalc:sigmaYp=sigyp
	Variable/G root:SRCalc:dUnLe=UnLe
end
//__________________________________________________________________________________________
Function FindBs()
//Initialize and find b2 and b3
	String savedDataFolder = GetDataFolder(1)		// save current data folder
	if(datafolderexists("root:SRCalc:")==0)
		print "Folder not found, will create"
		FillSR()
	endif
	SetDataFolder savedDataFolder

	Variable SoM1=NumVarOrDefault("root:SRCalc:dSoM1",31300)
	Variable SoGrX=NumVarOrDefault("root:SRCalc:dSoGrX",39700)
	Variable GrEx=NumVarOrDefault("root:SRCalc:dGrEx", 20000)
	Variable He=NumVarOrDefault("root:SRCalc:dHe", 15)
	Variable OpEner=NumVarOrDefault("SOpEner",800)
	Variable Opc=NumVarOrDefault("SOpc", 2.2)
	Variable Order=NumVarOrDefault("SOrder", 1)
	Variable lmm=NumVarOrDefault("Slmm", 1200)
	Variable V_Flag
	Variable V_Root
	
	Prompt SoM1, "dSoM1"
	Prompt SoGrX, "dSoGr. Equal to dSoM1 if collimated"
	Prompt GrEx, "Distance grating exit slit"
	Prompt He, "Height change mono"
	Prompt OpEner, "Optimization energy eV"
	Prompt  Opc, "c at optimization energy"
	Prompt  Order, "Diffraction order"
	Prompt  lmm, "lines/mm"
	doPrompt savedDataFolder, SoM1,SoGrX, GrEx, He, OpEner, Opc, Order, lmm
	if (V_Flag)
		return -1								// User canceled
	endif
	
	Variable/G root:SRCalc:dSoM1=SoM1
	Variable/G root:SRCalc:dSoGrX=SoGrX
	Variable/G root:SRCalc:dGrEx=GrEx
	Variable/G root:SRCalc:dHe=He			
	Variable/G SOpEner=OpEner
	Variable/G SOpc=Opc		
	Variable/G SOrder=Order
	Variable/G Slmm=lmm
	Variable/G b2			//b2
	Variable/G b3			//b3
	Make/O/N=7 par
	par[0]=AlphaFromCEnergyF(OPc,OpEner,lmm,Order)
	par[2]=BetaFromCEnergyF(OPc,OpEner,lmm,Order)
	if(SoM1==SoGrX)
		par[1]=inf
	else
		par[1]=SoGrX
	endif	
	par[3]=GrEx
	par[4]=Order
	par[5]=lmm
	par[6]=OpEner
	FindRoots /L=0 /H=1e-3/T=1e-13 f20PG, par
	b2=V_root
	FindRoots /L=0 /H=1e-6/T=1e-16 f30PG, par
	b3=V_root
end

//__________________________________________________________________________________________
Function CalcAll()
	String savedDataFolder = GetDataFolder(1)		// save current data folder
	Make/O/N=7 par
	NVar SOpc
	NVar sOrder
	NVar Slmm
	NVar b2
	Make/n=2/O W_Root
	NVar dSoM1=root:SRCalc:dSoM1
	NVar dSoGrX=root:SRCalc:dSoGrX
	NVar dGrEx=root:SRCalc:dGrEx
	NVar Slmm
	NVar SOrder

	Variable eMin=NumVarOrDefault("SeMin",200)
	Variable eMax=NumVarOrDefault("SeMax",2000)
	Variable nPo=NumVarOrDefault("SnPo",50)
	Variable SEGR=NumVarOrDefault("sSeGr",1e-7)
	Variable SEPM=NumVarOrDefault("sSEPM",2e-7)
	Variable Ex=NumVarOrDefault("sEx",0.01)
	Variable ToRe=NumVarOrDefault("sTore",1e4)
	Variable alp1
	Variable Bet1
	Variable V_Flag
	Variable V_Root

	Variable i
	prompt eMin, "Min Energy"
	prompt eMax, "Max Energy"
	prompt nPo, "Number energy points"
	prompt SEGR, "RMS slope error grating rad"
	prompt SEPM,  "RMS slope error mirror rad"
	prompt Ex, "Exit slits mm"
	prompt ToRe, "Total Resolving power"	
	DoPrompt savedDataFolder, eMin, eMax, nPo,	SEGR, SEPM,Ex,ToRe
	if (V_Flag)
		return -1								// User canceled
	endif

	Make/O/N=(nPo) Energies
	Variable/G SeMin=eMin
	Variable/G SeMax=eMax
	Variable/G SnPo=nPo
	Variable/G sSEGR=SEGR
	Variable/G sSEPM=SEPM
	Variable/G sEx=Ex
	Variable/G sToRe=ToRe
	SetScale/I x SeMin,SeMax,"", Energies
	Energies=x
//	Duplicate/O Energies alp,bet,angam,cVa, betm, lam
	Duplicate/O Energies alp,bet,angam,cVa, lam
	Duplicate/O Energies rEnTa, rExTa,rToTa,rSEGRTa,rSEPMTa,slit,slitForRP
	lam=eV_to_mmF(Energies)
	Make/O/N=5 val
	val[0]=dGrEx
	val[1]=sOrder
	val[2]=slmm
	val[4]=b2
	i=0
	do
		if(dSoM1==dSoGrX)				//Collimated case
			bet[i]=-Acos(sqrt(-2*b2*sOrder*slmm*eV_to_mmF(energies[i])*dGrEx))
			alp[i]=asin(sOrder*slmm*eV_to_mmF(energies[i])-sin(bet[i]))
			bet[i]*=180/pi
			alp[i]*=180/pi
		else
			val[3]=energies[i]
			alp1=AlphaFromCEnergyF(SOPc,Energies[i],Slmm,SOrder)
			bet1=BetaFromCEnergyF(SOPc,Energies[i],Slmm,SOrder)
			FindRoots/Q /X={alp1,bet1} /T=1e-11 /I=500 f20PG1,val, GrEq, val
			alp[i]=W_root[0]
			bet[i]=W_root[1]
		endif
		i+=1
	while (i<SnPo)		
	cVa=cosd(bet)/cosd(alp)
	angam=0.5*(alp-bet)
//	betm=-bet

	rEnTa=2.7*RlEn(lam,alp,Slmm,sigUn(Energies,1),dSoGrX)
	rExTa=RlEx (lam,bet,Slmm,sEx,dGrEx)
	rSEGRTa=RlSeGr (lam,alp,bet,Slmm,sSEGr)
	rSEPMTa=RlPar1 (lam,alp,Slmm,sSEPM)
	rToTa=sqrt(rEnTa^2+rExTa^2+rSEGRTa^2+rSEPMTa^2)
	i=0
	par[2]=Slmm
	par[3]=dGrEx
	do 
		par[0]= lam[i]
		par[1]=bet[i]
		par[4]=energies[i]
		par[5]=i
		FindRoots/Q /L=0 /H=1 /T=1e-6 findSlit, par
		slit[i]=V_root
		i=i+1
	while (i<1)	
	Variable hi
	Variable lo
	hi=slit[0]
	lo=hi*0.5	
	do 
		par[0]= lam[i]
		par[1]=bet[i]
		par[4]=energies[i]
		par[5]=i
		FindRoots/Q /L=(lo) /H=(hi) /T=1e-6 findSlit, par
		if (v_flag == 0)
			slit[i]=V_root
			hi=slit[i]
			lo=hi*0.5
		else
			slit[i]=inf
			hi=0
			lo=1	
		endif	
		i=i+1
		
	while (i<SnPo)			
	slitForRP=RlEx (lam,bet,Slmm,slit,dGrEx)
	Display rSEPMTa,rSEGRTa,rToTa,rExTa,rEnTa vs Energies
	execute/Q/Z "ResTerms()"
	Legend/C/N=text0/F=0/A=MC
	CreateOrUpdateCVal()
end

//__________________________________________________________________________________________
Function ShowVal()
	String savedDataFolder = GetDataFolder(1)		// save current data folder
	NVar b2
	NVar b3
	NVar dSoGrX=root:SRCalc:dSoGrX
	NVar dGrEx=root:SRCalc:dGrEx
	NVar Slmm
	NVar SOrder
	NVar seMin
	NVar seMax
	NVar sSEGR
	NVar sSEPM
	NVar sEx
	NVar sToRe
	NVar SOpEner
	NVar SOpc
	Variable b2a=b2
	Variable b3a=b3
	Variable SoGrX=dSoGrX
	Variable GrEx=dGrEx
	Variable lmm=Slmm
	Variable Order=SOrder
	Variable eMin=seMin
	Variable eMax=semax
	Variable SEGR=sSEGR
	Variable SEPM=sSEPM
	Variable Ex=sEx
	Variable ToRe=sToRe
	Variable OpEner=SOpEner
	Variable Opc=SOpc
	Prompt b2a, "b2"
	Prompt b3a, "b3"
	Prompt OpEner, "Optimization energy"
	Prompt Opc, "Optimized c"
	prompt  lmm, "line density"
//	prompt eMin, "Min Energy"
//	prompt eMax, "Max Energy"
	prompt SEGR, "RMS slope error grating µrad"
	prompt SEPM,  "RMS slope error mirror µrad"
	prompt Ex, "Exit slits mm"
	prompt ToRe, "Total Resolving power"
	DoPrompt savedDataFolder, b2a, b3a, OpEner, Opc, lmm,  SEGR, SEPM,Ex,ToRe

end

//__________________________________________________________________________________________
Function GetParRayTrace()
	String savedDataFolder = GetDataFolder(1)		// save current data folder
	NVar SOpc
	NVar sOrder
	NVar Slmm
	NVar b2
	Make/n=2/O W_Root
	NVar dSoGrX=root:SRCalc:dSoGrX
	NVar dGrEx=root:SRCalc:dGrEx
	NVar Slmm
	NVar SOrder
	Variable/G seMin
	Variable/G seMax
	Variable/G snPo
	Variable/G sSEGR
	Variable/G sSEPM
	Variable/G sEx
	Variable/G sToRe
	Variable eMin
	Variable eMax
	Variable nPo
	Variable SEGR
	Variable SEPM
	Variable Ex
	Variable ToRe
	Variable alp1
	Variable Bet1
	Variable V_Flag
	Variable V_Root
	
	Variable i
	eMin=SeMin
	eMax=SeMax
	nPo=SnPo
	SEGR=sSEGR
	SEPM=sSEPM
	Ex=sEx
	ToRe=sToRe

	prompt eMin, "Min Energy"
	prompt eMax, "Max Energy"
	prompt nPo, "Number energy points"
	prompt SEGR, "RMS slope error grating µrad"
	prompt SEPM,  "RMS slope error mirror µrad"
	prompt Ex, "Exit slits mm"
	prompt ToRe, "Total Resolving power"	
	DoPrompt savedDataFolder, eMin, eMax, nPo,	SEGR, SEPM,Ex,ToRe
	if (V_Flag)
		return -1								// User canceled
	endif
	end
	Make/O/N=(nPo) Energies
	SeMin=eMin
	SeMax=eMax
	SnPo=nPo
	sSEGR=SEGR
	sSEPM=SEPM
	sEx=Ex
	sToRe=ToRe
	SetScale/I x SeMin,SeMax,"", Energies
	Energies=x
	Duplicate/O Energies alp,bet,angam,cVa, betm, lam
	Duplicate/O Energies rEnTa, rExTa,rToTa,rSEGRTa,rSEPMTa,slit,slitForRP
	lam=eV_to_mmF(Energies)
	Make/O/N=5 val
	val[0]=dGrEx
	val[1]=sOrder
	val[2]=slmm
	val[4]=b2
	i=0
	do
		val[3]=energies[i]
		alp1=AlphaFromCEnergyF(SOPc,Energies[i],Slmm,SOrder)
		bet1=BetaFromCEnergyF(SOPc,Energies[i],Slmm,SOrder)
		FindRoots/Q/X={alp1,bet1} /T=1e-12 /I=500 f20PG1,val, GrEq, val
		alp[i]=W_root[0]
		bet[i]=W_root[1]
		i+=1
	while (i<SnPo)			
	cVa=cosd(bet)/cosd(alp)
	angam=0.5*(alp-bet)
	betm=-bet

	rEnTa=2.7*RlEn(lam,alp,Slmm,sigUn(Energies,1),dSoGrX)
	rExTa=RlEx (lam,bet,Slmm,sEx,dGrEx)
	rSEGRTa=RlSeGr (lam,alp,bet,Slmm,sSEGr)
	rSEPMTa=RlPar1 (lam,alp,Slmm,sSEPM)
	rToTa=sqrt(rEnTa^2+rExTa^2+rSEGRTa^2+rSEPMTa^2)
	i=0
	par[2]=Slmm
	par[3]=dGrEx
	do 
		par[0]= lam[i]
		par[1]=bet[i]
		par[4]=energies[i]
		par[5]=i
		FindRoots/Q /L=0 /H=0.2 /T=1e-6 findSlit, par
		slit[i]=V_root
		slitForRP[i]=RlEx (lam,bet,Slmm,slit[i],dGrEx)
		i=i+1
	while (i<1)	
	Variable hi
	Variable lo
	hi=slit[0]
	lo=hi*0.5	
	do 
		par[0]= lam[i]
		par[1]=bet[i]
		par[4]=energies[i]
		par[5]=i
		FindRoots/Q /L=(lo) /H=(hi) /T=1e-6 findSlit, par
		slit[i]=V_root
		slitForRP[i]=RlEx (lam,bet,Slmm,slit[i],dGrEx)
		hi=slit[i]
		lo=hi*0.5	
		i=i+1
	while (i<SnPo)			

end
//////////////////////////////////////////////////////////////////////////////
Function CreateOrUpdateCVal() 
//Will print the value of c and the number of l/m in the foremost graph.
	String dfSav
	String nfol
	String fitText

	Wave w=WaveRefIndexed("",0,1)
	dfSav = GetDataFolder(1)
	nfol=GetWavesDataFolder(w,1)
	SetDataFolder nfol
	NVAR Slmm
	NVAR Sopc
	sprintf fitText, "l/mm=%g, c=%g", SLmm,Sopc 
	TextBox/C/N=FitResults fitText
	TextBox/C/N=FitResults/F=0
	SetDataFolder dfSav
End 

//____________________________________________________________________________
Function eV_to_mmF(x)
Variable x
return 12398.52e-7/x
end

//____________________________________________________________________________
//RlEx
//____________________________________________________________________________
Function RlEx (lam,Bet,k,sEx,efF)
// ÊReturns resolution in eV due to exit slit
Variable lam,Bet,k,sEx,efF
Return (sEx * Cosd(Bet)) / (k * efF * lam)*eV_to_mmF(lam)
End

//____________________________________________________________________________
//RlEn
//____________________________________________________________________________
Function RlEn (lam,alpha,k,sEn,r)
// ÊReturns resolution in eV due to entrance slit
Variable lam,alpha,k,sEn,r
Return (sEn * Cosd(alpha)) / (k * r * lam)*eV_to_mmF(lam)
End

//____________________________________________________________________________
//RlSeGr
//____________________________________________________________________________
Function RlSeGr (lam,alpha,Bet,k,sig)
// ÊReturns resolution in eV due to slope errors on the grating
Variable lam,alpha,Bet,k,sig
Return 2*2.7 * sig * Cosd((alpha + Bet) / 2 ) * Cosd((alpha - Bet ) / 2 ) / (k* lam)*eV_to_mmF(lam)
End

//____________________________________________________________________________
//RlPar1
//____________________________________________________________________________
Function RlPar1 (lam,alpha,k,sig)
// ÊReturns resolution in eV Êdue to slope errors in a mirror before the grating
Variable lam,alpha,k,sig
Return (2*2.7 * sig*Cosd(alpha)) / (k * lam)*eV_to_mmF(lam)
End

//____________________________________________________________________________
// AlphaFromCEnergyF
//____________________________________________________________________________
Function AlphaFromCEnergyF(c,Energy,k,order)
Variable c, Energy,k,order
Variable flag=0
Variable V_Flag
Variable V_Root

if(c==1)
c=nan
Energy=nan
k=nan
order=1
flag=1
Prompt c, "c value"
Prompt Energy, "Energy in eV"
Prompt k, "Line density mm**-1"
Prompt order, "Diffraction order"
doPrompt "Geting alpha", c,Energy,k,order
if (V_Flag)
return -1
// User canceled
endif
endif
variable a=12398.52e-7/Energy*k*order
variable alpha
variable c2=c*c
alpha=asin((a-sqrt(a*a*c2+1-2*c2+c2*c2))/(1-c2))*180/pi
if(flag==1)
printf "alpha=%15.9g\r", alpha
endif
return alpha
end

//____________________________________________________________________________
//BetaFromCEnergyF
//____________________________________________________________________________
Function BetaFromCEnergyF(c,Energy,k,order)
Variable c, Energy,k,order
Variable flag=0
Variable V_Flag
Variable V_Root

if(c==1)
c=nan
Energy=nan
k=nan
order=1
flag=1
Prompt c, "c value"
Prompt Energy, "Energy in eV"
Prompt k, "Line density mm**-1"
Prompt order, "Diffraction order"
doPrompt "Geting alpha", c,Energy,k,order
if (V_Flag)
return -1
// User canceled
endif
endif
variable a=12398.52e-7/Energy*k*order
Variable betaA
variable c2=1/(c*c)
betaA=asin((a-sqrt(a*a*c2+1-2*c2+c2*c2))/(1-c2))*180/pi
if (flag==1)
printf "beta=%15.9g\r", betaA
endif
return betaA
end

//____________________________________________________________________________
Function cosd(x)
variable x
return cos(x*pi/180)
end


//____________________________________________________________________________
Function sind(x)
variable x
return sin(x*pi/180)
end

//____________________________________________________________________________
Function tand(x)
variable x
return tan(x*pi/180)
end