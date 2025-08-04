class Mactoro < Formula
  include Language::Python::Virtualenv

  desc "Powerful macOS automation tool for window control and action recording"
  homepage "https://github.com/kory-/mactoro"
  url "https://github.com/kory-/mactoro/archive/v0.1.0.tar.gz"
  sha256 "PLACEHOLDER_SHA256"
  license "MIT"
  head "https://github.com/kory-/mactoro.git", branch: "main"

  depends_on "python@3.11"

  resource "click" do
    url "https://files.pythonhosted.org/packages/96/d3/f04c7bfcf5c1862a2a5b845c6b2b360488cf47af55dfa79c98f6a6bf98b5/click-8.1.7.tar.gz"
    sha256 "ca9853ad459e787e2192211578cc907e7594e294c7ccc834310722b41b9ca6de"
  end

  resource "pillow" do
    url "https://files.pythonhosted.org/packages/f8/3e/32cbd0129a28686621434cbf17bb64bf1458bfb838f1f668262fefce145c/pillow-10.2.0.tar.gz"
    sha256 "e87f0b2c78157e12d7686b27d63c070fd65d994e8ddae6f328e0dcf4a0cd007e"
  end

  resource "pyautogui" do
    url "https://files.pythonhosted.org/packages/65/ff/cdae0a8c2118a0de74b6cf4cbcdcaf8fd25857e6c3f205ce4b1794b27814/PyAutoGUI-0.9.54.tar.gz"
    sha256 "dd1d29e8fd118941cb193f74df57e5c6ff8e9253b99c7b04f39cfc69f3ae04b2"
  end

  resource "pynput" do
    url "https://files.pythonhosted.org/packages/d7/74/a231bca942b1cd9c4bb707788be325a61d26c7998bd25e88dc510d4b55c7/pynput-1.7.6.tar.gz"
    sha256 "3a5726546da54116b687785d38b1db56997ce1d28e53e8d22fc656d8b92e533c"
  end

  resource "pyobjc-core" do
    url "https://files.pythonhosted.org/packages/e8/e9/0b85c81e2b441267bca707b5d89f56c2f02578ef8f3eafddf0e0c0b8848c/pyobjc_core-11.1.tar.gz"
    sha256 "b63d4d90c5df7e762f34739b39cc55bc63dbcf9fb2fb3f2671e528488c7a87fe"
  end

  resource "pyobjc-framework-Cocoa" do
    url "https://files.pythonhosted.org/packages/4b/c5/7a866d24bc026f79239b74d05e2cf3088b03263da66d53d1b4cf5207f5ae/pyobjc_framework_cocoa-11.1.tar.gz"
    sha256 "87df76b9b73e7ca699a828ff112564b59251bb9bbe72e610e670a4dc9940d038"
  end

  resource "pyobjc-framework-Quartz" do
    url "https://files.pythonhosted.org/packages/c7/ac/6308fec6c9ffeda9942fef72724f4094c6df4933560f512e63eac37ebd30/pyobjc_framework_quartz-11.1.tar.gz"
    sha256 "a57f35ccfc22ad48c87c5932818e583777ff7276605fef6afad0ac0741169f75"
  end

  resource "opencv-python" do
    url "https://files.pythonhosted.org/packages/ac/71/25c98e634b6bdeca4727c7f6d6927b056080668c5008ad3c8fc9e7f8f6ec/opencv-python-4.12.0.88.tar.gz"
    sha256 "8b738389cede219405f6f3880b851efa3415ccd674752219377353f017d2994d"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/mactoro", "--version"
    
    # Test window list command
    output = shell_output("#{bin}/mactoro window list 2>&1", 1)
    assert_match "Currently open windows", output
  end
end