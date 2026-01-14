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
  version "0.9.5"

  # Download pre-built binary from GitHub Releases
  url "https://github.com/pradeeproark/pensieve/releases/download/v0.9.5/pensieve-0.9.5-macos"
  sha256 "9a2c52b75e83767b1f1f15b36f32d49ec3930190c72f69bb9ad28634b68f29b2"

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
