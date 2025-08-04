class Mactoro < Formula
  include Language::Python::Virtualenv

  desc "Powerful macOS automation tool for window control and action recording"
  homepage "https://github.com/yourusername/mactoro"
  url "https://github.com/yourusername/mactoro/archive/v0.1.0.tar.gz"
  sha256 "YOUR_SHA256_HERE"
  license "MIT"

  depends_on "python@3.11"
  depends_on "pillow"

  resource "pyobjc-core" do
    url "https://files.pythonhosted.org/packages/source/p/pyobjc-core/pyobjc-core-9.2.tar.gz"
    sha256 "YOUR_SHA256_HERE"
  end

  resource "pyobjc-framework-Cocoa" do
    url "https://files.pythonhosted.org/packages/source/p/pyobjc-framework-Cocoa/pyobjc-framework-Cocoa-9.2.tar.gz"
    sha256 "YOUR_SHA256_HERE"
  end

  resource "pyobjc-framework-Quartz" do
    url "https://files.pythonhosted.org/packages/source/p/pyobjc-framework-Quartz/pyobjc-framework-Quartz-9.2.tar.gz"
    sha256 "YOUR_SHA256_HERE"
  end

  resource "pyautogui" do
    url "https://files.pythonhosted.org/packages/source/P/PyAutoGUI/PyAutoGUI-0.9.54.tar.gz"
    sha256 "YOUR_SHA256_HERE"
  end

  resource "click" do
    url "https://files.pythonhosted.org/packages/source/c/click/click-8.1.7.tar.gz"
    sha256 "YOUR_SHA256_HERE"
  end

  resource "pynput" do
    url "https://files.pythonhosted.org/packages/source/p/pynput/pynput-1.7.6.tar.gz"
    sha256 "YOUR_SHA256_HERE"
  end

  resource "opencv-python" do
    url "https://files.pythonhosted.org/packages/source/o/opencv-python/opencv-python-4.8.1.78.tar.gz"
    sha256 "YOUR_SHA256_HERE"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/mactoro", "--version"
  end
end