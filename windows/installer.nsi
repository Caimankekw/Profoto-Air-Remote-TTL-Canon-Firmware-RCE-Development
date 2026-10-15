; SPDX-License-Identifier: AGPL-3.0-only
; Copyright (C) 2026 Caimankekw
Unicode true
!include "MUI2.nsh"
!define MUI_LANGDLL_ALWAYSSHOW
!define MUI_LANGDLL_ALLLANGUAGES
!define MUI_LANGDLL_WINDOWTITLE "Language / 语言"
!define MUI_LANGDLL_INFO "Choose a language / 请选择语言"
Name "Air Remote TTL-C AIR2-P8-FIX1 Custom Updater"
OutFile "${OUTPUT_EXE}"
InstallDir "$LOCALAPPDATA\Caimankekw\AirRemote-TTL-C\AIR2-P8-FIX1"
RequestExecutionLevel user
SetCompressor /SOLID lzma
SetCompressorDictSize 32
CRCCheck on
BrandingText "Caimankekw - experimental custom firmware, not an official Profoto release"
VIProductVersion "8.0.1.0"
VIAddVersionKey /LANG=1033 "ProductName" "Air Remote TTL-C AIR2-P8-FIX1 Custom Updater"
VIAddVersionKey /LANG=1033 "CompanyName" "Caimankekw"
VIAddVersionKey /LANG=1033 "FileDescription" "Experimental AIR2-P8-FIX1 firmware package; not an official release"
VIAddVersionKey /LANG=1033 "FileVersion" "8.0.1.0"
VIAddVersionKey /LANG=1033 "LegalCopyright" "Copyright 2026 Caimankekw; original components retain their notices"

!define MUI_WELCOMEPAGE_TITLE "$(WelcomeTitle)"
!define MUI_WELCOMEPAGE_TEXT "$(WelcomeText)"
!insertmacro MUI_PAGE_WELCOME
!define MUI_PAGE_HEADER_TEXT "$(DisclaimerTitle)"
!define MUI_PAGE_HEADER_SUBTEXT "$(DisclaimerSubtitle)"
!define MUI_LICENSEPAGE_TEXT_TOP "$(DisclaimerTop)"
!define MUI_LICENSEPAGE_TEXT_BOTTOM "$(DisclaimerBottom)"
!define MUI_LICENSEPAGE_BUTTON "$(ContinueText)"
!insertmacro MUI_PAGE_LICENSE "$(DisclaimerText)"
!define MUI_PAGE_HEADER_TEXT "$(LicenseTitle)"
!define MUI_PAGE_HEADER_SUBTEXT "$(LicenseSubtitle)"
!define MUI_LICENSEPAGE_TEXT_TOP "$(LicenseTop)"
!define MUI_LICENSEPAGE_TEXT_BOTTOM "$(LicenseBottom)"
!define MUI_LICENSEPAGE_BUTTON "$(ContinueText)"
!insertmacro MUI_PAGE_LICENSE "${TEXT_DIR}\LICENSE.txt"
!define MUI_PAGE_CUSTOMFUNCTION_LEAVE CheckDestination
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_FUNCTION LaunchUpdater
!define MUI_FINISHPAGE_RUN_NOTCHECKED
!define MUI_FINISHPAGE_RUN_TEXT "$(OpenUpdater)"
!define MUI_FINISHPAGE_TEXT "$(FinishText)"
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "SimpChinese"

LicenseLangString DisclaimerText ${LANG_ENGLISH} "${TEXT_DIR}\DISCLAIMER.en.txt"
LicenseLangString DisclaimerText ${LANG_SIMPCHINESE} "${TEXT_DIR}\DISCLAIMER.zh-CN.txt"
LangString WelcomeTitle ${LANG_ENGLISH} "AIR2-P8-FIX1 custom firmware updater"
LangString WelcomeTitle ${LANG_SIMPCHINESE} "AIR2-P8-FIX1 自定义固件更新包"
LangString WelcomeText ${LANG_ENGLISH} "Developer: Caimankekw. Release: 2026-10-16.$\r$\nExperimental Air Remote TTL-C (Canon) firmware; not an official Profoto release.$\r$\n$\r$\nFIX1 fixes AIR1 expiry while busy. It has not been booted or camera-tested on hardware.$\r$\n$\r$\nThis wizard only extracts files. It does not automatically install drivers, access USB or flash a device. Read the disclaimer, license and extracted README before opening the updater."
LangString WelcomeText ${LANG_SIMPCHINESE} "开发者：Caimankekw。发布日期：2026-10-16。$\r$\n适用于 Air Remote TTL-C（Canon）的实验固件，不是 Profoto 官方发布。$\r$\n$\r$\nFIX1 修复 AIR1 到期遇忙时数值残留的问题，尚未经过真机开机或相机测试。$\r$\n$\r$\n本向导仅解压文件，不自动安装驱动、访问 USB 或刷写设备。请阅读免责声明、许可和解压目录中的说明，再打开更新器。"
LangString DisclaimerTitle ${LANG_ENGLISH} "Experimental firmware disclaimer"
LangString DisclaimerTitle ${LANG_SIMPCHINESE} "测试固件免责声明"
LangString DisclaimerSubtitle ${LANG_ENGLISH} "Read before deciding whether to use this firmware."
LangString DisclaimerSubtitle ${LANG_SIMPCHINESE} "请先阅读，再自主决定是否使用本固件。"
LangString DisclaimerTop ${LANG_ENGLISH} "The complete English and Chinese documents are included alongside LICENSE and bilingual NOTICE files."
LangString DisclaimerTop ${LANG_SIMPCHINESE} "完整中英文免责声明与 LICENSE、中英文 NOTICE 一同包含在解压目录。"
LangString DisclaimerBottom ${LANG_ENGLISH} "Continue extracts the package; it does not authorize or perform a device update."
LangString DisclaimerBottom ${LANG_SIMPCHINESE} "继续用于解压本包，不会执行设备更新。"
LangString LicenseTitle ${LANG_ENGLISH} "AGPL-3.0-only license"
LangString LicenseTitle ${LANG_SIMPCHINESE} "AGPL-3.0-only 开源协议"
LangString LicenseSubtitle ${LANG_ENGLISH} "Original custom code by Caimankekw."
LangString LicenseSubtitle ${LANG_SIMPCHINESE} "Caimankekw 原创自定义代码。"
LangString LicenseTop ${LANG_ENGLISH} "AGPL covers this project's original custom code only. Vendor firmware, updater and other third-party materials retain their own terms."
LangString LicenseTop ${LANG_SIMPCHINESE} "AGPL 仅适用于本项目原创自定义代码。厂商固件、更新器及其他第三方材料保留原有条款。"
LangString LicenseBottom ${LANG_ENGLISH} "See NOTICE.md for scope. Corresponding source is included as source.zip."
LangString LicenseBottom ${LANG_SIMPCHINESE} "许可范围见 NOTICE.zh-CN.md；对应源码随包提供为 source.zip。"
LangString ContinueText ${LANG_ENGLISH} "Continue"
LangString ContinueText ${LANG_SIMPCHINESE} "继续"
LangString OpenUpdater ${LANG_ENGLISH} "Open the AIR2-P8-FIX1 updater (no automatic update)"
LangString OpenUpdater ${LANG_SIMPCHINESE} "打开 AIR2-P8-FIX1 更新器（不会自动更新）"
LangString FinishText ${LANG_ENGLISH} "Extraction is complete. Read README.md or README.zh-CN.md before updating.$\r$\n$\r$\nOpening the updater is optional and unchecked by default. Follow its original GUI instructions and click its update button yourself.$\r$\n$\r$\nThe original C11 recovery updater is in restore_original."
LangString FinishText ${LANG_SIMPCHINESE} "解压完成。更新前请阅读 README.zh-CN.md 或 README.md。$\r$\n$\r$\n打开更新器是可选操作，默认不勾选。请遵循其原有图形界面说明，由你手动点击更新。$\r$\n$\r$\n原厂 C11 恢复程序位于 restore_original。"
LangString DestinationNotEmpty ${LANG_ENGLISH} "Choose a new folder that does not already exist. This package does not overwrite an existing installation."
LangString DestinationNotEmpty ${LANG_SIMPCHINESE} "请选择尚不存在的新目录。本包不会覆盖已有安装。"
LangString LaunchFailed ${LANG_ENGLISH} "The updater could not be opened. Open it manually from the extracted folder."
LangString LaunchFailed ${LANG_SIMPCHINESE} "无法打开更新器，请从解压目录手动打开。"

Function .onInit
  SetShellVarContext current
  !insertmacro MUI_LANGDLL_DISPLAY
FunctionEnd

Function CheckDestination
  IfFileExists "$INSTDIR\*.*" occupied empty
occupied:
  MessageBox MB_OK|MB_ICONEXCLAMATION "$(DestinationNotEmpty)"
  Abort
empty:
FunctionEnd

Section "Extract AIR2-P8-FIX1"
  Call CheckDestination
  SetOutPath "$INSTDIR"
  SetOverwrite off
  File /r "${PACKAGE_DIR}\*.*"
SectionEnd

Function LaunchUpdater
  SetOutPath "$INSTDIR"
  ClearErrors
  Exec '"$INSTDIR\AirRemote_TTL_C_C11_AIR2_P8_FIX1_Caimankekw_EXPERIMENTAL.exe"'
  IfErrors 0 done
  MessageBox MB_OK|MB_ICONEXCLAMATION "$(LaunchFailed)"
done:
FunctionEnd
