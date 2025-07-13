from django.conf import settings


class ImageErrors:
    IMAGE_FILE_SIZE_TOO_BIG = (
        10,
        f"Image file size too big, expected <= {settings.MAX_IMAGE_SIZE} bytes"
    )
    INVALID_IMAGE_SIZE = (
        11,
        f"Invalid image width/height, expected them to be in range "
        f"{settings.MIN_IMAGE_DIMENSION}px..{settings.MAX_IMAGE_DIMENSION}px"
    )


# def process_image(image):
#     """
#     :return: (processed image, error response)
#     """
#     if image.size > settings.MAX_IMAGE_SIZE:
#         return None, Response(
#             status=status.HTTP_400_BAD_REQUEST,
#             data=error_detail(*ImageErrors.IMAGE_FILE_SIZE_TOO_BIG)
#         )
#     width, height = image.image.size
#     if not (
#             settings.MIN_IMAGE_DIMENSION <= width <=
#             settings.MAX_IMAGE_DIMENSION and
#             settings.MIN_IMAGE_DIMENSION <= height <=
#             settings.MAX_IMAGE_DIMENSION
#     ):
#         return None, Response(
#             status=status.HTTP_400_BAD_REQUEST,
#             data=error_detail(*ImageErrors.INVALID_IMAGE_SIZE)
#         )
#     return image, None
