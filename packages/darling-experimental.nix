{ pkgs }:
let
  languageProvider = import ./darling-language.nix { inherit pkgs; };
  languageFrameworks = import ./darling-naturallanguage.nix { inherit pkgs; };
  manifest = builtins.fromJSON (builtins.readFile ./darling-swift-payload.json);
  payloads = map (file: {
    inherit (file) path;
    source = pkgs.fetchurl {
      url = "https://media.githubusercontent.com/media/${manifest.repository}/${manifest.revision}/${file.path}";
      inherit (file) sha256;
    };
  }) manifest.files;
  swiftCore = (builtins.head (builtins.filter (file: file.path == "libswiftCore.dylib") payloads)).source;
  extension = pkgs.runCommand "darling-swift-experimental-${builtins.substring 0 8 manifest.revision}" {
    nativeBuildInputs = [ pkgs.llvmPackages_18.clang-unwrapped pkgs.llvmPackages_18.lld ];
  } ''
    cp -a ${languageFrameworks}/. $out/
    chmod -R u+w $out
    mkdir -p $out/usr/lib/swift
    ${pkgs.lib.concatMapStringsSep "\n" (file:
      let target = if pkgs.lib.hasInfix ".framework/" file.path
                   then "System/Library/Frameworks/${file.path}" else "usr/lib/swift/${file.path}";
      in ''install -D -m 644 ${file.source} "$out/${target}"'') payloads}
    for framework in Combine CryptoKit; do
      ln -s A $out/System/Library/Frameworks/$framework.framework/Versions/Current
      ln -s Versions/Current/$framework $out/System/Library/Frameworks/$framework.framework/$framework
    done
    ln -s libswiftCore.dylib $out/usr/lib/swift/libswiftCompatibilitySpan.dylib
    clang -target x86_64-apple-macosx11.0 -c ${../modules/lickintosh/mac-apps/swift-core-compat.S} -o compat.o
    ld64.lld -dylib -arch x86_64 -platform_version macos 11.0 11.0 \
      -install_name /usr/lib/swift/libswiftCoreCompat.dylib \
      -compatibility_version 1.0.0 -current_version 1.0.0 \
      -undefined dynamic_lookup -reexport_library ${swiftCore} compat.o \
      -o $out/usr/lib/swift/libswiftCoreCompat.dylib
    cp ${../modules/lickintosh/mac-apps/mt19937-64.h} mt19937-64.h
    clang -target x86_64-apple-macosx11.0 -fno-objc-arc -fblocks \
      -I . -c ${../modules/lickintosh/mac-apps/GameplayKit.m} -o gameplay.o
    mkdir -p $out/System/Library/Frameworks/GameplayKit.framework/Versions/A
    ld64.lld -dylib -arch x86_64 -platform_version macos 11.0 11.0 \
      -install_name /System/Library/Frameworks/GameplayKit.framework/Versions/A/GameplayKit \
      -compatibility_version 1.0.0 -current_version 1.0.0 -undefined dynamic_lookup \
      -needed_library ${../modules/lickintosh/mac-apps/Foundation-link.tbd} gameplay.o \
      -o $out/System/Library/Frameworks/GameplayKit.framework/Versions/A/GameplayKit
    ln -s A $out/System/Library/Frameworks/GameplayKit.framework/Versions/Current
    ln -s Versions/Current/GameplayKit $out/System/Library/Frameworks/GameplayKit.framework/GameplayKit
  '';
  runtime = import ./darling-runtime.nix {
    inherit pkgs extension languageProvider;
    commandName = "darling-experimental";
    profileName = "darling-experimental";
  };
  notices = pkgs.runCommand "darling-swift-experimental-notices" {} ''
    mkdir -p $out/share/doc/darling-experimental
    cp ${../modules/lickintosh/mac-apps/licenses/Swift.txt} $out/share/doc/darling-experimental/Swift-LICENSE.txt
    cp ${../modules/lickintosh/mac-apps/licenses/OpenCombine.txt} $out/share/doc/darling-experimental/OpenCombine-LICENSE.txt
    cp ${./darling-swift-payload.json} $out/share/doc/darling-experimental/payload-manifest.json
  '';
in pkgs.symlinkJoin {
  name = "darling-experimental-with-notices";
  paths = [ runtime notices languageProvider ];
}
