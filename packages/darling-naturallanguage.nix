{ pkgs }:
pkgs.runCommand "quickintosh-naturallanguage" {
  nativeBuildInputs = [ pkgs.llvmPackages_18.clang-unwrapped pkgs.llvmPackages_18.lld ];
} ''
  cp ${../modules/lickintosh/mac-apps/Foundation-NL.h} Foundation-NL.h
  clang -target x86_64-apple-macosx11.0 -fno-objc-arc -fblocks -O2 -I . \
    -c ${../modules/lickintosh/mac-apps/NaturalLanguage.m} -o language.o
  destination=$out/System/Library/Frameworks/NaturalLanguage.framework
  mkdir -p "$destination/Versions/A"
  ld64.lld -dylib -arch x86_64 -platform_version macos 11.0 11.0 \
    -install_name /System/Library/Frameworks/NaturalLanguage.framework/Versions/A/NaturalLanguage \
    -compatibility_version 1.0.0 -current_version 1.0.0 -undefined dynamic_lookup \
    -needed_library ${../modules/lickintosh/mac-apps/Foundation-link.tbd} language.o \
    -o "$destination/Versions/A/NaturalLanguage"
  ln -s A "$destination/Versions/Current"
  ln -s Versions/Current/NaturalLanguage "$destination/NaturalLanguage"
  clang -target x86_64-apple-macosx11.0 -fno-objc-arc -fblocks -O2 -I . \
    -c ${../modules/lickintosh/mac-apps/QuickLookThumbnailing.m} -o thumbnail.o
  destination=$out/System/Library/Frameworks/QuickLookThumbnailing.framework
  mkdir -p "$destination/Versions/A"
  ld64.lld -dylib -arch x86_64 -platform_version macos 11.0 11.0 \
    -install_name /System/Library/Frameworks/QuickLookThumbnailing.framework/Versions/A/QuickLookThumbnailing \
    -compatibility_version 1.0.0 -current_version 1.0.0 -undefined dynamic_lookup \
    -needed_library ${../modules/lickintosh/mac-apps/Foundation-link.tbd} \
    -needed_library ${../modules/lickintosh/mac-apps/AppKit-link.tbd} thumbnail.o \
    -o "$destination/Versions/A/QuickLookThumbnailing"
  ln -s A "$destination/Versions/Current"
  ln -s Versions/Current/QuickLookThumbnailing "$destination/QuickLookThumbnailing"
''
