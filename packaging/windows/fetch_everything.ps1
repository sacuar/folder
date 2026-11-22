param([string]$Destination='dist/Folder/everything')
$ErrorActionPreference='Stop'
$base='https://www.voidtools.com'
$engine='Everything-1.4.1.1032.x64.zip'
$cli='ES-1.1.0.37.x64.zip'
$tmp=Join-Path ([IO.Path]::GetTempPath()) ('folder-search-'+[guid]::NewGuid())
New-Item -ItemType Directory -Force $tmp,$Destination|Out-Null
try {
 $hashFile=Join-Path $tmp 'hashes.txt'
 Invoke-WebRequest "$base/Everything-1.4.1.1032.sha256" -OutFile $hashFile
 foreach($name in @($engine,$cli)){
  $zip=Join-Path $tmp $name
  Invoke-WebRequest "$base/$name" -OutFile $zip
  if($name -eq $engine){
   $line=Get-Content $hashFile|Where-Object{$_ -match [regex]::Escape($name)+'\s*$'}|Select-Object -First 1
   $expected=[regex]::Match([string]$line,'[a-fA-F0-9]{64}').Value
   if(!$expected -or (Get-FileHash $zip -Algorithm SHA256).Hash -ine $expected){throw 'Everything distribution SHA256 mismatch'}
  }
  $dir=Join-Path $tmp ($name+'.unzip')
  Expand-Archive $zip -DestinationPath $dir
  $exeName=if($name -eq $engine){'Everything.exe'}else{'es.exe'}
  $exe=Get-ChildItem $dir -Recurse -File -Filter $exeName|Select-Object -First 1
  if(!$exe){throw "$exeName not found"}
  if($name -eq $engine){
   $sig=Get-AuthenticodeSignature $exe.FullName
   if($sig.Status -ne 'Valid'){throw 'Everything executable signature is not valid'}
  }
  Copy-Item $exe.FullName $Destination -Force
  # Retain vendor notices in version-specific subfolders.
  $notices=Join-Path $Destination ($name+'.notices')
  New-Item -ItemType Directory -Force $notices|Out-Null
  Get-ChildItem $dir -Recurse -File|Where-Object {$_.Extension -in '.txt','.md' -or $_.Name -match 'licen|copying'}|ForEach-Object{Copy-Item $_.FullName $notices -Force}
  (Get-FileHash $zip -Algorithm SHA256|Format-List|Out-String)|Set-Content (Join-Path $notices 'download-sha256.txt')
 }
 Invoke-WebRequest "$base/License.txt" -OutFile (Join-Path $Destination 'Everything-LICENSE.txt')
}finally{Remove-Item $tmp -Recurse -Force}
