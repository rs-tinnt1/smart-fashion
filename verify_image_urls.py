"""
Quick test to verify image URLs are accessible
"""
import httpx

def test_gallery_image_urls():
    """Test that gallery images are accessible"""
    # Get gallery data
    response = httpx.get("http://localhost:8000/api/gallery", timeout=10.0)
    assert response.status_code == 200
    
    data = response.json()
    print(f"\n✓ Gallery API returned {data['count']} images")
    
    if data['count'] > 0:
        # Test first image URL
        first_image = data['images'][0]
        original_url = first_image['original_url']
        
        print(f"✓ Testing URL: {original_url}")
        
        # Verify URL format
        assert "localhost:9000" in original_url, f"URL should use localhost:9000, got: {original_url}"
        assert "minio:9000" not in original_url, f"URL should NOT use minio:9000"
        
        # Test URL accessibility
        url_response = httpx.get(original_url, timeout=10.0)
        assert url_response.status_code == 200, f"URL should be accessible, got: {url_response.status_code}"
        
        print(f"✓ Image URL is accessible (HTTP {url_response.status_code})")
        print(f"✓ Content-Type: {url_response.headers.get('content-type')}")
        print(f"✓ Content-Length: {len(url_response.content)} bytes")
        
        # Test output URL if exists
        if first_image.get('output_url'):
            output_url = first_image['output_url']
            print(f"\n✓ Testing output URL: {output_url}")
            output_response = httpx.get(output_url, timeout=10.0)
            assert output_response.status_code == 200
            print(f"✓ Output image URL is accessible (HTTP {output_response.status_code})")
    else:
        print("⚠ No images in gallery to test")

if __name__ == "__main__":
    test_gallery_image_urls()
    print("\n✅ All image URL tests passed!")
