# Homebrew Formula for Pensieve
#
# This file should be placed in the `pradeeproark/homebrew-pensieve` repository
# at the path: Formula/pensieve.rb
#
# To use:
# 1. Create repository: pradeeproark/homebrew-pensieve
# 2. Add this file to Formula/pensieve.rb
# 3. Update VERSION, URL, and SHA256 after each release
# 4. Users install with: brew tap pradeeproark/pensieve && brew install pensieve

class Pensieve < Formula
  desc "Memory recording tool for Claude Code agents"
  homepage "https://github.com/pradeeproark/pensieve"
  version "0.7.0"

  # Download pre-built binary from GitHub Releases
  url "https://github.com/pradeeproark/pensieve/releases/download/v0.7.0/pensieve-0.6.0-macos"
  sha256 "6a41ce962329fdcfcc91e11c91211d3b898efe7bac22e84d2ad87c4e445c7c70"

  # No dependencies - it's a self-contained binary

  def install
    # Rename the downloaded file to 'pensieve' and install to bin
    bin.install "pensieve-0.6.0-macos" => "pensieve"
  end

  test do
    # Test that the executable runs and outputs version
    assert_match "pensieve, version #{version}", shell_output("#{bin}/pensieve --version")
  end
end
